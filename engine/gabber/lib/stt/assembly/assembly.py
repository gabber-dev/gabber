# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import json
import logging
from typing import Any

import aiohttp

from gabber.core.runtime_types import AudioClip, AudioFrame
from utils import short_uuid

from ..stt import (
    STT,
    STTEvent,
    STTEvent_EndOfTurn,
    STTEvent_SpeechStarted,
    STTEvent_Transcription,
)


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
        trans_id: str = short_uuid()
        offset_samples: int = 0
        frames: list[AudioFrame] = []
        start_ms: float = -1
        end_ms: float = -1
        running_words: list[str] = []

        async def rec_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal start_ms, end_ms, trans_id, running_words, frames, offset_samples
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
                    formatted = data.get("turn_is_formatted", False)
                    words: list[dict[str, Any]] = data.get("words", [])
                    first_word = words[0] if words else None
                    last_word = words[-1] if words else None

                    if last_word:
                        end_ms = last_word["end"]

                    if start_ms < 0 and first_word:
                        start_ms = first_word["start"] - 600  # Adjust
                        if start_ms < 0:
                            start_ms = 0
                        self._output_queue.put_nowait(
                            STTEvent_SpeechStarted(id=trans_id)
                        )

                    new_word_cnt = len(words) - len(running_words)
                    new_words: list[str] = []
                    if new_word_cnt > 0:
                        new_words = [w["text"] for w in words[:new_word_cnt]]
                        running_words.extend(new_words)

                    self._output_queue.put_nowait(
                        STTEvent_Transcription(
                            trans_id,
                            delta_text=" ".join(new_words),
                            running_text=transcript,
                        )
                    )

                    if end_of_turn and formatted:
                        offset_time_ms = offset_samples * 1000.0 / 24000.0
                        if not frames:
                            logging.warning(
                                "No frames available for end of turn processing"
                            )
                            continue

                        # Remove frames that are before the start of the turn
                        while (
                            frames
                            and (
                                offset_time_ms
                                + frames[0].data_24000hz.duration * 1000.0
                            )
                            < start_ms
                        ):
                            f = frames.pop(0)
                            offset_samples += f.data_24000hz.sample_count
                            offset_time_ms = (offset_samples * 1000.0) / 24000.0

                        # Only include frames that are within the turn
                        clip_frames: list[AudioFrame] = []
                        while (
                            frames
                            and (
                                offset_time_ms
                                + frames[0].data_24000hz.duration * 1000.0
                            )
                            < end_ms
                        ):
                            f = frames.pop(0)
                            clip_frames.append(f)
                            offset_samples += f.data_24000hz.sample_count
                            offset_time_ms = offset_samples * 1000.0 / 24000.0

                        clip = AudioClip(
                            audio=clip_frames,
                            transcription=transcript,
                        )
                        self._output_queue.put_nowait(
                            STTEvent_EndOfTurn(id=trans_id, clip=clip)
                        )
                        trans_id = short_uuid()
                        running_words = []
                        start_ms = -1
                        end_ms = -1

                elif msg_type == "Termination":
                    pass

        async def send_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            audio_bytes = b""
            running_frames: list[AudioFrame] = []
            dur = 0
            while True:
                if ws.closed:
                    break
                item = await self._process_queue.get()
                if item is None:
                    return

                audio_bytes += item.data_24000hz.data.tobytes()
                running_frames.append(item)
                dur += item.data_24000hz.duration
                # Send in 100ms chunks
                if dur > 0.1:
                    for f in running_frames:
                        frames.append(f)
                    running_frames.clear()
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
                    "format_turns": "true",
                    "min_end_of_turn_silence_when_confident": 600,
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
