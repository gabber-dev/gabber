# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import time
from typing import cast

from core import node, pad, runtime_types
from lib.tts import TTS as BaseTTS
from lib.tts import CartesiaTTS, ElevenLabsTTS, GabberTTS


class TTS(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Converts text to speech using Gabber's native TTS model"

    @classmethod
    def get_metadata(cls) -> node.NodeMetadata:
        return node.NodeMetadata(
            primary="ai", secondary="audio", tags=["tts", "speech", "gabber"]
        )

    async def resolve_pads(self):
        # Migrate from old version
        PADS_TO_REMOVE = ["text_stream", "complete_text"]
        self.pads = [p for p in self.pads if p.get_id() not in PADS_TO_REMOVE]

        service = cast(pad.PropertySinkPad, self.get_pad("service"))
        if not service:
            service = pad.PropertySinkPad(
                id="service",
                group="service",
                owner_node=self,
                type_constraints=[
                    pad.types.Enum(options=["gabber", "cartesia", "elevenlabs"])
                ],
            )
            self.pads.append(service)

        api_key = cast(pad.PropertySinkPad, self.get_pad("api_key"))
        if not api_key:
            api_key = pad.PropertySinkPad(
                id="api_key",
                group="api_key",
                owner_node=self,
                type_constraints=[pad.types.Secret(options=self.secrets)],
            )
            self.pads.append(api_key)

        voice_id = cast(pad.PropertySinkPad, self.get_pad("voice_id"))
        if not voice_id:
            voice_id = pad.PropertySinkPad(
                id="voice_id",
                group="voice_id",
                owner_node=self,
                type_constraints=[pad.types.String()],
            )
            self.pads.append(voice_id)

        text_sink = cast(pad.StatelessSinkPad, self.get_pad("text"))
        if text_sink is None:
            text_sink = pad.StatelessSinkPad(
                id="text",
                group="text",
                owner_node=self,
                type_constraints=[pad.types.TextStream()],
            )
            self.pads.append(text_sink)

        prev_pad = text_sink.get_previous_pad()
        if prev_pad:
            tcs = prev_pad.get_type_constraints()
            tcs = pad.types.INTERSECTION(tcs, text_sink.get_type_constraints())
            text_sink.set_type_constraints(tcs)
        else:
            text_sink.set_type_constraints([pad.types.TextStream(), pad.types.String()])

        audio_source = cast(pad.StatelessSourcePad, self.get_pad("audio"))
        if audio_source is None:
            audio_source = pad.StatelessSourcePad(
                id="audio",
                group="audio",
                owner_node=self,
                type_constraints=[pad.types.Audio()],
            )
            self.pads.append(audio_source)

        cancel_trigger = cast(pad.StatelessSinkPad, self.get_pad("cancel_trigger"))
        if cancel_trigger is None:
            cancel_trigger = pad.StatelessSinkPad(
                id="cancel_trigger",
                group="cancel_trigger",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(cancel_trigger)

        final_transcription_source = cast(
            pad.StatelessSourcePad, self.get_pad("complete_transcription")
        )
        if final_transcription_source is None:
            final_transcription_source = pad.StatelessSourcePad(
                id="complete_transcription",
                group="complete_transcription",
                owner_node=self,
                type_constraints=[pad.types.String()],
            )
            self.pads.append(final_transcription_source)

    async def run(self):
        api_key_pad = cast(pad.PropertySinkPad, self.get_pad_required("api_key"))
        secret = api_key_pad.get_value()
        api_key = await self.secret_provider.resolve_secret(secret)
        service = cast(pad.PropertySinkPad, self.get_pad_required("service"))
        voice_id = cast(pad.PropertySinkPad, self.get_pad_required("voice_id"))
        audio_source = cast(pad.StatelessSourcePad, self.get_pad_required("audio"))
        text_sink = cast(pad.StatelessSinkPad, self.get_pad_required("text"))
        cancel_trigger = cast(
            pad.StatelessSinkPad, self.get_pad_required("cancel_trigger")
        )
        final_transcription_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("complete_transcription")
        )
        tts: BaseTTS
        if service.get_value() == "gabber":
            tts = GabberTTS(api_key=api_key)
        elif service.get_value() == "elevenlabs":
            tts = ElevenLabsTTS(api_key=api_key, voice=voice_id.get_value())
        elif service.get_value() == "cartesia":
            tts = CartesiaTTS(api_key=api_key)
        else:
            raise ValueError(f"Unknown TTS service: {service.get_value()}")
        job_queue = asyncio.Queue[TTSJob | None]()
        running_job: TTSJob | None = None

        tts_run_task = asyncio.create_task(tts.run())

        async def cancel_task():
            nonlocal running_job
            async for it in cancel_trigger:
                if (
                    running_job is not None
                    and it.ctx.original_request != running_job.ctx.original_request
                ):
                    logging.debug(
                        f"Cancelling TTS job {running_job.ctx.original_request.id} from queue"
                    )
                    running_job.eos()
                    running_job.cancel()
                    running_job = None

                left_over_job: TTSJob | None = None
                while not job_queue.empty():
                    job = await job_queue.get()
                    if job is None:
                        break
                    if job.ctx.original_request == it.ctx.original_request:
                        left_over_job = job
                        continue
                    logging.debug(
                        f"Cancelling TTS job {job.ctx.original_request.id} from queue"
                    )
                    job.eos()
                    job.cancel()

                if left_over_job is not None:
                    job_queue.put_nowait(left_over_job)

                it.ctx.complete()

        async def text_task():
            async for item in text_sink:
                if isinstance(item.value, runtime_types.TextStream):
                    pass
                    job = TTSJob(tts, item.ctx, voice=voice_id.get_value())
                    job_queue.put_nowait(job)
                    async for text in item.value:
                        job.push_text(text)
                    job.eos()
                elif isinstance(item.value, str):
                    job = TTSJob(tts, item.ctx, voice=voice_id.get_value())
                    job_queue.put_nowait(job)
                    job.push_text(item.value)
                    job.eos()

        async def job_task():
            nonlocal running_job
            while True:
                new_job = await job_queue.get()
                if new_job is None:
                    break

                running_job = new_job
                played_time = 0
                clock_start_time: float | None = None
                new_job.ctx.snooze_timeout(
                    120.0
                )  # Speech playout can take a while so we snooze the timeout. TODO: make this tied to the actual audio playout duration
                async for audio_frame in new_job:
                    if clock_start_time is None:
                        clock_start_time = time.time()
                    audio_source.push_item(audio_frame, new_job.ctx)
                    played_time += audio_frame.original_data.duration

                    # Don't go faster than real-time
                    while (played_time + clock_start_time) - time.time() > 0.25:
                        await asyncio.sleep(0.1)

                final_transcription_source.push_item(new_job.spoken_text, new_job.ctx)
                new_job.ctx.complete()

        await asyncio.gather(
            text_task(),
            job_task(),
            cancel_task(),
            tts_run_task,
        )


class TTSJob:
    def __init__(self, tts: BaseTTS, ctx: pad.RequestContext, voice: str):
        self.ctx = ctx
        self._tts = tts
        self._session = self._tts.start_session(voice=voice)
        self._running_text = ""

    def cancel(self):
        self._session.cancel()

    def push_text(self, text: str):
        self._running_text += text
        self._session.push_text(text)

    def eos(self):
        self._session.eos()

    def __aiter__(self):
        return self

    async def __anext__(self):
        async for audio_frame in self._session:
            return audio_frame

        raise StopAsyncIteration

    @property
    def spoken_text(self) -> str:
        return self._running_text
