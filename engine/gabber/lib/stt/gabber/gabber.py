# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import json
import logging
import base64
from typing import Any
from .messages import (
    RequestPayload_StartSession,
    RequestPayload_AudioData,
    ResponsePayload,
    ResponsePayload_Error,
    ResponsePayload_FinalTranscription,
    ResponsePayload_InterimTranscription,
    ResponsePayload_SpeakingStarted,
    Request,
)

import aiohttp

from gabber.core.runtime_types import AudioClip, AudioFrame
from gabber.utils import short_uuid

from ..stt import (
    STT,
    STTEvent,
    STTEvent_EndOfTurn,
    STTEvent_SpeechStarted,
    STTEvent_Transcription,
)


class Gabber(STT):
    def __init__(self, *, logger: logging.Logger | logging.LoggerAdapter):
        self.logger = logger
        self._process_queue = asyncio.Queue[AudioFrame | None]()
        self._closed = False
        self._output_queue = asyncio.Queue[STTEvent | None]()

    def push_audio(self, audio: AudioFrame) -> None:
        self._process_queue.put_nowait(audio)

    async def run(self) -> None:
        while not self._closed:
            try:
                await self._run_ws()
            except Exception as e:
                logging.error("WebSocket connection error: %s", exc_info=e)

            await asyncio.sleep(1)

    async def _run_ws(self) -> None:
        session_id = short_uuid()
        offset_samples: int = 0
        frames: list[AudioFrame] = []
        start_ms: float = -1
        end_ms: float = -1
        running_words: list[str] = []

        async def rec_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal start_ms, end_ms, running_words, frames, offset_samples
            while not self._closed:
                if ws.closed:
                    break
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.CLOSED:
                    self.logger.info("WebSocket closed")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error("WebSocket error: %s", msg.data)
                    break
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    pass

                data = json.loads(msg.data)
                self.logger.info(f"Received message: {data}")

        async def send_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            audio_bytes = b""
            start_payload = RequestPayload_StartSession(sample_rate=16000)
            start_msg = Request(payload=start_payload, session_id=session_id)
            await ws.send_str(start_msg.model_dump_json())
            while True:
                if ws.closed:
                    break
                item = await self._process_queue.get()
                if item is None:
                    return

                audio_bytes += item.data_16000hz.data.tobytes()
                dur = len(audio_bytes) / (16000 * 2)
                if dur < 0.1:
                    continue
                for i in range(0, len(audio_bytes), 3200):
                    chunk = audio_bytes[i : i + 3200]
                    if len(chunk) != 3200:
                        break
                    b64_audio = base64.b64encode(chunk).decode("utf-8")
                    payload = RequestPayload_AudioData(b64_data=b64_audio)
                    msg = Request(payload=payload, session_id=session_id)
                    await ws.send_str(msg.model_dump_json())

        async def keepalive_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            while not self._closed:
                await asyncio.sleep(2)
                if ws.closed:
                    break
                await ws.ping()

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                "ws://localhost:7004"
            ) as ws:  # Adjust port as needed
                await asyncio.gather(
                    rec_task(ws),
                    send_task(ws),
                    keepalive_task(ws),
                )

    def __aiter__(self):
        return self

    async def __anext__(self) -> STTEvent:
        event = await self._output_queue.get()
        if event is None:
            raise StopAsyncIteration
        return event
