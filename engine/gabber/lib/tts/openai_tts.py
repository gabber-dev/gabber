# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging

import numpy as np
from openai import AsyncOpenAI

from gabber.core.runtime_types import AudioFrame, AudioFrameData
from gabber.lib.audio import Resampler

from .tts import TTS, TTSSession


class OpenAITTS(TTS):
    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        super().__init__()
        self.logger = logger
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)
        self.task_queue: asyncio.Queue[asyncio.Task | None] = asyncio.Queue()

    def start_session(self, *, voice: str) -> TTSSession:
        session = OpenAITTSSession(
            voice=voice, model=self.model, client=self.client, logger=self.logger
        )
        self.task_queue.put_nowait(asyncio.create_task(session.run()))
        return session

    async def run(self):
        while True:
            task = await self.task_queue.get()
            if task is None:
                break
            await task


class OpenAITTSSession(TTSSession):
    def __init__(
        self,
        *,
        voice: str,
        model: str,
        client: AsyncOpenAI,
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        super().__init__(voice=voice, logger=self.logger)
        self.client = client
        self.voice = voice
        self.model = model

    async def run(self):
        r_16000hz = Resampler(16000)
        r_44100hz = Resampler(44100)
        r_48000hz = Resampler(48000)
        text = ""
        while True:
            chunk = await self._text_queue.get()
            if chunk is None or self._closed:
                break
            text += chunk

        buffer_bytes = 24000  # 500ms buffer at 24kHz
        async with self.client.audio.speech.with_streaming_response.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="pcm",
            instructions="Speak in a cheerful and positive tone.",
        ) as response:
            running_chunk = b""
            async for audio_chunk in response.iter_bytes():
                running_chunk += audio_chunk
                # Give it 500ms to start before producing a chunk
                if len(running_chunk) % 2 == 0 and len(running_chunk) >= buffer_bytes:
                    frame_data_24000 = AudioFrameData(
                        data=np.frombuffer(running_chunk, dtype=np.int16).reshape(
                            1, -1
                        ),
                        sample_rate=24000,
                        num_channels=1,
                    )
                    frame_data_16000 = r_16000hz.push_audio(frame_data_24000)
                    frame_data_44100 = r_44100hz.push_audio(frame_data_24000)
                    frame_data_48000 = r_48000hz.push_audio(frame_data_24000)
                    frame = AudioFrame(
                        original_data=frame_data_24000,
                        data_16000hz=frame_data_16000,
                        data_24000hz=frame_data_24000,
                        data_44100hz=frame_data_44100,
                        data_48000hz=frame_data_48000,
                    )
                    running_chunk = b""
                    self._output_queue.put_nowait(frame)

                buffer_bytes = 240

            if len(running_chunk):
                frame_data_24000 = AudioFrameData(
                    data=np.frombuffer(running_chunk, dtype=np.int16).reshape(1, -1),
                    sample_rate=24000,
                    num_channels=1,
                )
                frame_data_16000 = r_16000hz.push_audio(frame_data_24000)
                frame_data_44100 = r_44100hz.push_audio(frame_data_24000)
                frame_data_48000 = r_48000hz.push_audio(frame_data_24000)
                frame = AudioFrame(
                    original_data=frame_data_24000,
                    data_16000hz=frame_data_16000,
                    data_24000hz=frame_data_24000,
                    data_44100hz=frame_data_44100,
                    data_48000hz=frame_data_48000,
                )
                self._output_queue.put_nowait(frame)

            self._output_queue.put_nowait(None)

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self._output_queue.get()
        if item is None or self._closed:
            raise StopAsyncIteration

        if isinstance(item, Exception):
            raise item

        return item
