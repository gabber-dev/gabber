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

    async def resolve_pads(self):
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

        text_stream_sink = cast(pad.StatelessSinkPad, self.get_pad("text_stream"))
        if text_stream_sink is None:
            text_stream_sink = pad.StatelessSinkPad(
                id="text_stream",
                group="text_stream",
                owner_node=self,
                type_constraints=[pad.types.TextStream()],
            )
            self.pads.append(text_stream_sink)

        complete_text_sink = cast(pad.StatelessSinkPad, self.get_pad("complete_text"))
        if complete_text_sink is None:
            complete_text_sink = pad.StatelessSinkPad(
                id="complete_text",
                group="complete_text",
                owner_node=self,
                type_constraints=[pad.types.String()],
            )
            self.pads.append(complete_text_sink)

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
        text_stream_sink = cast(
            pad.StatelessSinkPad, self.get_pad_required("text_stream")
        )
        complete_text_sink = cast(
            pad.StatelessSinkPad, self.get_pad_required("complete_text")
        )
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

        async def text_stream_task():
            async for item in text_stream_sink:
                job = TTSJob(item.ctx, voice=voice_id.get_value())
                job_queue.put_nowait(job)
                async for text in item.value:
                    job.push_text(text)
                job.eos()

        async def complete_text_task():
            async for text in complete_text_sink:
                job = TTSJob(text.ctx, voice=voice_id.get_value())
                job_queue.put_nowait(job)
                job.push_text(text.value)
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
                async for bytes_24000 in new_job:
                    frame_data_24000 = runtime_types.AudioFrameData(
                        data=np.frombuffer(bytes_24000, dtype=np.int16).reshape(1, -1),
                        sample_rate=24000,
                        num_channels=1,
                    )
                    frame_data_16000 = r_16000hz.push_audio(frame_data_24000)
                    frame_data_44100 = r_44100hz.push_audio(frame_data_24000)
                    frame_data_48000 = r_48000hz.push_audio(frame_data_24000)
                    frame = runtime_types.AudioFrame(
                        original_data=frame_data_24000,
                        data_16000hz=frame_data_16000,
                        data_24000hz=frame_data_24000,
                        data_44100hz=frame_data_44100,
                        data_48000hz=frame_data_48000,
                    )
                    if clock_start_time is None:
                        clock_start_time = time.time()
                    audio_source.push_item(frame, new_job.ctx)
                    played_time += frame.original_data.duration

                    # Don't go faster than real-time
                    while (played_time + clock_start_time) - time.time() > 0.25:
                        await asyncio.sleep(0.1)

                final_transcription_source.push_item(new_job.spoken_text, new_job.ctx)
                new_job.ctx.complete()

        await asyncio.gather(
            complete_text_task(),
            text_stream_task(),
            job_task(),
            cancel_task(),
        )


class TTSJob:
    def __init__(self, ctx: pad.RequestContext, voice: str):
        self.ctx = ctx
        self._voice = voice
        self._running_text = ""
        self._buffer = ""
        self._pending_short = ""
        self._output_queue = asyncio.Queue[bytes | None]()
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

        try:
            async with aiohttp.ClientSession() as session:
                while True:
                    input_text = await self._inference_queue.get()

                    if input_text is None:
                        break
                    input_text = (
                        input_text + " ...."
                    )  # Adding these dots helps the early cutoff issue that kitten tts has
                    try:
                        async with session.post(
                            url, json={"text": input_text, "voice": self._voice}
                        ) as response:
                            if response.status != 200:
                                logging.error(
                                    f"Error in TTS request: {response.status} - {await response.text()}"
                                )
                                break

                            async for chunk in response.content.iter_any():
                                self._output_queue.put_nowait(chunk)
                    except Exception as e:
                        logging.error(f"Error during TTS request: {e}", exc_info=True)
                        break
        except asyncio.CancelledError:
            logging.debug("TTS job cancelled")

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
