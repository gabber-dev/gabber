# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import json
import logging
from typing import Any, cast

import aiohttp
import msgpack

from core.runtime_types import AudioClip, AudioFrame
from utils import short_uuid

from ..stt import (
    STT,
    STTEvent,
    STTEvent_EndOfTurn,
    STTEvent_SpeechStarted,
    STTEvent_Transcription,
)

STEPS_PER_SECOND = 12.5
FLUSH_ZEROS_SECONDS = 1
COOLDOWN_SECONDS = 0.5
DRIFT_THRESHOLD = 3
PRE_BUFFER_SECONDS = 5.0

FLUSH_FRAME = AudioFrame.silence(FLUSH_ZEROS_SECONDS)


class Assembly(STT):
    def __init__(self, *, api_key: str):
        self._api_key = api_key
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
        async def rec_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            while not self._closed:
                if ws.closed:
                    break
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.CLOSED:
                    logging.info("WebSocket closed")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logging.error("WebSocket error: %s", msg.data)
                    break
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    pass

                data = json.loads(msg.data)
                msg_type = data.get("type")
                if msg_type == "Begin":
                    logging.info("STT session started")
                elif msg_type == "Turn":
                    transcript = data.get("transcript", "")
                    end_of_turn = data.get("end_of_turn", False)
                    words: list[dict[str, Any]] = data.get("words", [])
                    last_word = words[-1] if words else None
                    last_ms = last_word["end"] if last_word else -1
                    if last_ms > 0:
                        pass
                    if transcript:
                        self._output_queue.put_nowait(
                            STTEvent_Transcription(transcript)
                        )
                elif msg_type == "Termination":
                    pass

        async def send_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            audio_bytes = b""
            dur = 0
            while True:
                if ws.closed:
                    break
                item = await self._process_queue.get()
                if item is None:
                    return

                audio_bytes += item.data_24000hz.data.tobytes()
                dur += item.data_24000hz.duration
                if dur > 0.1:
                    await ws.send_bytes(audio_bytes)
                    audio_bytes = b""
                    dur = 0

        async def keepalive_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            while not self._closed:
                await asyncio.sleep(2)
                if ws.closed:
                    break
                await ws.ping()

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                "wss://streaming.assemblyai.com/v3/ws",
                headers={"Authorization": self._api_key},
                params={
                    "sample_rate": 24000,
                    "encoding": "pcm_s16le",
                },
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

    def endpoint_cooldown(self, prob, last_word) -> None:
        """
        Signal the end of the audio stream.
        """
        self._process_queue.put_nowait(None)
