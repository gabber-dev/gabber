# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging

from .tts import TTS, TTSSession


class NoopTTS(TTS):
    def __init__(
        self,
        *,
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        super().__init__()
        self.logger = logger
        self.task_queue: asyncio.Queue[asyncio.Task | None] = asyncio.Queue()

    def start_session(self, *, voice: str) -> TTSSession:
        tts_session = TTSSession(voice=voice, logger=self.logger)
        return tts_session

    async def session_task(self, session: TTSSession):
        while True:
            txt = await session._text_queue.get()
            if txt is None:
                break

        session._output_queue.put_nowait(None)

    async def run(self):
        while True:
            task = await self.task_queue.get()
            if task is None:
                break
            await task
