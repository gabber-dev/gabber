# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import time
from typing import cast

from gabber.core import node, pad
from gabber.core.types import runtime, pad_constraints
from gabber.lib.tts import TTS as BaseTTS
from gabber.lib.tts import CartesiaTTS, ElevenLabsTTS, GabberTTS, OpenAITTS


class TTS(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Converts text to speech using Gabber's native TTS model"

    @classmethod
    def get_metadata(cls) -> node.NodeMetadata:
        return node.NodeMetadata(
            primary="ai", secondary="audio", tags=["tts", "speech", "gabber"]
        )

    def resolve_pads(self):
        # Migrate from old version
        PADS_TO_REMOVE = ["text_stream", "complete_text"]
        self.pads = [p for p in self.pads if p.get_id() not in PADS_TO_REMOVE]

        service = cast(pad.PropertySinkPad, self.get_pad("service"))
        if not service:
            service = pad.PropertySinkPad(
                id="service",
                group="service",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.Enum(
                        options=["gabber", "cartesia", "elevenlabs", "openai"]
                    )
                ],
                value=runtime.Enum(value="gabber"),
            )

        api_key = cast(pad.PropertySinkPad[str], self.get_pad("api_key"))
        if not api_key:
            api_key = pad.PropertySinkPad(
                id="api_key",
                group="api_key",
                owner_node=self,
                default_type_constraints=[pad_constraints.Secret(options=self.secrets)],
                value=None,
            )

        voice_id = cast(pad.PropertySinkPad, self.get_pad("voice_id"))
        if not voice_id:
            voice_id = pad.PropertySinkPad(
                id="voice_id",
                group="voice_id",
                owner_node=self,
                default_type_constraints=[pad_constraints.String()],
                value="626c3b02-2d2a-4a93-b3e7-be35fd2b95cd",  # Tara
            )

        text_sink = cast(pad.StatelessSinkPad, self.get_pad("text"))
        if text_sink is None:
            text_sink = pad.StatelessSinkPad(
                id="text",
                group="text",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.TextStream(),
                    pad_constraints.String(),
                ],
            )

        audio_source = cast(pad.StatelessSourcePad, self.get_pad("audio"))
        if audio_source is None:
            audio_source = pad.StatelessSourcePad(
                id="audio",
                group="audio",
                owner_node=self,
                default_type_constraints=[pad_constraints.Audio()],
            )

        cancel_trigger = cast(pad.StatelessSinkPad, self.get_pad("cancel_trigger"))
        if cancel_trigger is None:
            cancel_trigger = pad.StatelessSinkPad(
                id="cancel_trigger",
                group="cancel_trigger",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        final_transcription_source = cast(
            pad.StatelessSourcePad, self.get_pad("complete_transcription")
        )
        if final_transcription_source is None:
            final_transcription_source = pad.StatelessSourcePad(
                id="complete_transcription",
                group="complete_transcription",
                owner_node=self,
                default_type_constraints=[pad_constraints.String()],
            )

        tts_started_source = cast(pad.StatelessSourcePad, self.get_pad("tts_started"))
        if tts_started_source is None:
            tts_started_source = pad.StatelessSourcePad(
                id="tts_started",
                group="tts_started",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        tts_ended_source = cast(pad.StatelessSourcePad, self.get_pad("tts_ended"))
        if tts_ended_source is None:
            tts_ended_source = pad.StatelessSourcePad(
                id="tts_ended",
                group="tts_ended",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        is_talking = cast(pad.PropertySourcePad, self.get_pad("is_talking"))
        if is_talking is None:
            is_talking = pad.PropertySourcePad(
                id="is_talking",
                group="is_talking",
                owner_node=self,
                default_type_constraints=[pad_constraints.Boolean()],
                value=False,
            )

        self.pads = [
            service,
            api_key,
            voice_id,
            text_sink,
            audio_source,
            cancel_trigger,
            final_transcription_source,
            tts_started_source,
            tts_ended_source,
            is_talking,
        ]

    async def run(self):
        api_key_pad = self.get_property_sink_pad_required(runtime.Secret, "api_key")
        secret = api_key_pad.get_value()
        api_key = await self.secret_provider.resolve_secret(secret.secret_id)
        service = self.get_property_sink_pad_required(runtime.Enum, "service")
        voice_id = self.get_property_sink_pad_required(str, "voice_id")
        audio_source = self.get_stateless_source_pad_required(
            runtime.AudioFrame, "audio"
        )
        text_sink = cast(
            pad.StatelessSinkPad[runtime.TextStream | str],
            self.get_pad_required("text"),
        )
        cancel_trigger = cast(
            pad.StatelessSinkPad, self.get_pad_required("cancel_trigger")
        )
        final_transcription_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("complete_transcription")
        )
        tts_started_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("tts_started")
        )
        tts_ended_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("tts_ended")
        )
        is_talking = cast(
            pad.PropertySourcePad, self.get_pad_required("is_talking")
        )
        tts: BaseTTS
        if service.get_value().value == "gabber":
            tts = GabberTTS(api_key=api_key, logger=self.logger)
        elif service.get_value().value == "elevenlabs":
            tts = ElevenLabsTTS(
                api_key=api_key, voice=voice_id.get_value(), logger=self.logger
            )
        elif service.get_value().value == "cartesia":
            tts = CartesiaTTS(api_key=api_key, logger=self.logger)
        elif service.get_value() == "openai":
            tts = OpenAITTS(
                model="gpt-4o-mini-tts", api_key=api_key, logger=self.logger
            )
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
                if isinstance(item.value, runtime.TextStream):
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
                is_talking.set_value(True)
                tts_started_source.push_item(runtime.Trigger(), new_job.ctx)
                try:
                    async for audio_frame in new_job:
                        if clock_start_time is None:
                            clock_start_time = time.time()
                        audio_source.push_item(audio_frame, new_job.ctx)
                        played_time += audio_frame.original_data.duration

                        # Don't go faster than real-time
                        while (played_time + clock_start_time) - time.time() > 0.25:
                            await asyncio.sleep(0.05)
                except Exception as e:
                    logging.error(f"Error occurred while processing TTS job: {e}")
                    final_transcription_source.push_item("", new_job.ctx)
                    is_talking.set_value(False)
                    tts_ended_source.push_item(runtime.Trigger(), new_job.ctx)
                    new_job.ctx.complete()
                    continue

                final_transcription_source.push_item(new_job.spoken_text, new_job.ctx)
                is_talking.set_value(False)
                tts_ended_source.push_item(runtime.Trigger(), new_job.ctx)
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
