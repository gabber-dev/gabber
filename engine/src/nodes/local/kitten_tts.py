# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import os
import aiohttp
import logging
import time
from typing import cast

from core import node, pad, runtime_types
from lib.audio import Resampler
import numpy as np

VOICES = [
    "expr-voice-2-m",
    "expr-voice-2-f",
    "expr-voice-3-m",
    "expr-voice-3-f",
    "expr-voice-4-m",
    "expr-voice-4-f",
    "expr-voice-5-m",
    "expr-voice-5-f",
]


class KittenTTS(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Converts text to speech using Gabber's native TTS model"

    @classmethod
    def get_metadata(cls) -> node.NodeMetadata:
        return node.NodeMetadata(
            primary="local", secondary="audio", tags=["tts", "speech", "gabber"]
        )

    def resolve_pads(self):
        # Migrate from old versions of this node
        REMOVE_PADS = [
            "text_stream",
            "complete_text",
        ]

        self.pads = [p for p in self.pads if p.get_id() not in REMOVE_PADS]

        voice_id = cast(pad.PropertySinkPad, self.get_pad("voice_id"))
        if not voice_id:
            voice_id = pad.PropertySinkPad(
                id="voice_id",
                group="voice_id",
                owner_node=self,
                type_constraints=[pad.types.Enum(options=VOICES)],
                value="expr-voice-2-m",
            )
            self.pads.append(voice_id)

        text_sink = cast(pad.StatelessSinkPad, self.get_pad("text"))
        if text_sink is None:
            text_sink = pad.StatelessSinkPad(
                id="text",
                group="text",
                owner_node=self,
                type_constraints=[pad.types.TextStream(), pad.types.String()],
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
        voice_id = cast(pad.PropertySinkPad, self.get_pad_required("voice_id"))
        audio_source = cast(pad.StatelessSourcePad, self.get_pad_required("audio"))
        text_sink = cast(pad.StatelessSinkPad, self.get_pad_required("text"))
        cancel_trigger = cast(
            pad.StatelessSinkPad, self.get_pad_required("cancel_trigger")
        )
        final_transcription_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("complete_transcription")
        )
        job_queue = asyncio.Queue[TTSJob | None]()
        running_job: TTSJob | None = None
        r_16000hz = Resampler(16000)
        r_44100hz = Resampler(44100)
        r_48000hz = Resampler(48000)

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
                if isinstance(item.value, str):
                    job = TTSJob(
                        ctx=item.ctx,
                        voice=voice_id.get_value(),
                        resampler_16000hz=r_16000hz,
                        resampler_44100hz=r_44100hz,
                        resampler_48000hz=r_48000hz,
                    )
                    job_queue.put_nowait(job)
                    job.push_text(item.value)
                    job.eos()
                elif isinstance(item.value, runtime_types.TextStream):
                    job = TTSJob(
                        ctx=item.ctx,
                        voice=voice_id.get_value(),
                        resampler_16000hz=r_16000hz,
                        resampler_44100hz=r_44100hz,
                        resampler_48000hz=r_48000hz,
                    )
                    job_queue.put_nowait(job)
                    async for text in item.value:
                        job.push_text(text)
                    job.eos()

        async def job_task():
            nonlocal running_job
            while True:
                new_job = await job_queue.get()
                if new_job is None:
                    break

                running_job = new_job
                new_job.ctx.snooze_timeout(
                    120.0
                )  # Speech playout can take a while so we snooze the timeout. TODO: make this tied to the actual audio playout duration
                async for frame in new_job:
                    audio_source.push_item(frame, new_job.ctx)

                final_transcription_source.push_item(new_job.spoken_text, new_job.ctx)
                new_job.ctx.complete()

        await asyncio.gather(
            text_task(),
            job_task(),
            cancel_task(),
        )


class TTSJob:
    def __init__(
        self,
        *,
        ctx: pad.RequestContext,
        voice: str,
        resampler_16000hz: Resampler,
        resampler_44100hz: Resampler,
        resampler_48000hz: Resampler,
    ):
        self.ctx = ctx
        self._resampler_16000hz = resampler_16000hz
        self._resampler_44100hz = resampler_44100hz
        self._resampler_48000hz = resampler_48000hz
        self._voice = voice
        self._running_text = ""
        self._buffer = ""
        self._pending_short = ""
        self._output_queue = asyncio.Queue[runtime_types.AudioFrame | None]()
        self._inference_queue = asyncio.Queue[str | None]()
        self._run_task = asyncio.create_task(self.run())

    def cancel(self):
        self._run_task.cancel()
        self._output_queue.put_nowait(None)

    def push_text(self, text: str):
        self._running_text += text
        self._buffer += text
        text_to_process = self._pending_short + self._buffer
        self._pending_short = ""
        self._buffer = ""
        sentences, remainder = self._extract_sentences(text_to_process)
        temp = ""
        for sentence in sentences:
            words = len(sentence.split())
            if words < 3:
                temp += (" " if temp else "") + sentence
            else:
                if temp:
                    to_push = temp + " " + sentence
                    self._inference_queue.put_nowait(to_push)
                    temp = ""
                else:
                    self._inference_queue.put_nowait(sentence)
        self._pending_short = temp
        self._buffer = remainder

    def _extract_sentences(self, text: str) -> tuple[list[str], str]:
        sentences = []
        pos = 0
        while pos < len(text):
            next_end = -1
            for punct in ".!?":
                p = text.find(punct, pos)
                if p != -1 and (next_end == -1 or p < next_end):
                    next_end = p
            if next_end == -1:
                break
            if next_end + 1 == len(text) or text[next_end + 1].isspace():
                sentence = text[pos : next_end + 1]
                sentence += " "
                sentences.append(sentence)
                pos = next_end + 1
                while pos < len(text) and text[pos].isspace():
                    pos += 1
            else:
                pos = next_end + 1
        remainder = text[pos:]
        return sentences, remainder

    def eos(self):
        text_to_push = self._pending_short + self._buffer
        if text_to_push:
            self._inference_queue.put_nowait(text_to_push)
        self._inference_queue.put_nowait(None)

    async def run(self):
        host = os.environ.get("KITTEN_TTS_HOST", "localhost")
        url = f"http://{host}:7003/tts"

        send_queue = asyncio.Queue[bytes | None]()

        async def generate():
            async with aiohttp.ClientSession() as session:
                while True:
                    input_text = await self._inference_queue.get()

                    if input_text is None:
                        break

                    if len(input_text) == 0:
                        continue

                    if input_text[-1] not in ".!?":
                        input_text += ". "

                    async with session.post(
                        url, json={"text": input_text, "voice": self._voice}
                    ) as response:
                        if response.status != 200:
                            logging.error(
                                f"Error in TTS request: {response.status} - {await response.text()}"
                            )
                            break

                        total_bytes = b""
                        async for bytes_24000 in response.content.iter_any():
                            total_bytes += bytes_24000
                            # 20ms
                            while len(total_bytes) >= 240 * 4:
                                chunk = total_bytes[: 240 * 4]
                                total_bytes = total_bytes[240 * 4 :]
                                send_queue.put_nowait(chunk)

                        if len(total_bytes) % 2 != 0:
                            total_bytes = total_bytes[:-1]
                        send_queue.put_nowait(total_bytes)
                        send_queue.put_nowait(None)

        async def push_response():
            clock_start_time: float | None = None
            played_time = 0.0
            while True:
                chunk = await send_queue.get()
                if chunk is None:
                    break
                data = np.frombuffer(chunk, dtype=np.int16).reshape(1, -1)
                num_samples = data.shape[1]
                frame_data_24000 = runtime_types.AudioFrameData(
                    data=data,
                    sample_rate=24000,
                    num_channels=1,
                )
                frame_data_16000 = self._resampler_16000hz.push_audio(frame_data_24000)
                frame_data_44100 = self._resampler_44100hz.push_audio(frame_data_24000)
                frame_data_48000 = self._resampler_48000hz.push_audio(frame_data_24000)
                frame = runtime_types.AudioFrame(
                    original_data=frame_data_24000,
                    data_16000hz=frame_data_16000,
                    data_24000hz=frame_data_24000,
                    data_44100hz=frame_data_44100,
                    data_48000hz=frame_data_48000,
                )
                if clock_start_time is None:
                    clock_start_time = time.time()
                played_time += num_samples / 24000.0
                self._output_queue.put_nowait(frame)

                # Don't go faster than real-time
                while (played_time + clock_start_time) - time.time() > 0.25:
                    await asyncio.sleep(0.05)

        try:
            await asyncio.gather(
                generate(),
                push_response(),
            )
        except asyncio.CancelledError:
            logging.debug("TTS job cancelled")
        except Exception as e:
            logging.error(f"Error in TTS job: {e}", exc_info=True)
        finally:
            self._output_queue.put_nowait(None)

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self._output_queue.get()
        if item is None:
            raise StopAsyncIteration
        return item

    @property
    def spoken_text(self) -> str:
        return self._running_text
