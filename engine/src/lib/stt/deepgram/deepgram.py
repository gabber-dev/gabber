# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import json
import logging
from urllib.parse import urlencode

import aiohttp

from core.runtime_types import AudioClip, AudioFrame
from utils import short_uuid

from ..stt import (
    STT,
    STTEvent,
    STTEvent_EndOfTurn,
    STTEvent_SpeechStarted,
    STTEvent_Transcription,
)


class Deepgram(STT):
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
        transcript: str = ""
        trans_id: str = short_uuid()
        offset_samples: int = 0
        frames: list[AudioFrame] = []
        start_ms: float = -1
        end_ms: float = -1
        running_words: list[str] = []

        def commit_transcription():
            nonlocal \
                start_ms, \
                end_ms, \
                trans_id, \
                running_words, \
                frames, \
                offset_samples, \
                transcript
            if transcript == "":
                running_words.clear()
                start_ms = -1
                end_ms = -1
                return

            offset_time_ms = offset_samples * 1000.0 / 24000.0
            if not frames:
                logging.warning("No frames available for end of turn processing")
                return

            # Remove frames that are before the start of the turn
            while (
                frames
                and (offset_time_ms + frames[0].data_24000hz.duration * 1000.0)
                < start_ms
            ):
                f = frames.pop(0)
                offset_samples += f.data_24000hz.sample_count
                offset_time_ms = (offset_samples * 1000.0) / 24000.0

            # Only include frames that are within the turn
            clip_frames: list[AudioFrame] = []
            while (
                frames
                and (offset_time_ms + frames[0].data_24000hz.duration * 1000.0) < end_ms
            ):
                f = frames.pop(0)
                clip_frames.append(f)
                offset_samples += f.data_24000hz.sample_count
                offset_time_ms = offset_samples * 1000.0 / 24000.0

            clip = AudioClip(
                audio=clip_frames,
                transcription=transcript,
            )
            self._output_queue.put_nowait(STTEvent_EndOfTurn(id=trans_id, clip=clip))
            trans_id = short_uuid()
            running_words = []
            start_ms = -1
            end_ms = -1

        async def rec_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal \
                start_ms, \
                end_ms, \
                trans_id, \
                running_words, \
                frames, \
                offset_samples, \
                transcript
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
                if msg_type == "Results":
                    is_final = data.get("is_final", False)
                    alternative = data.get("channel", {}).get("alternatives", [{}])[0]
                    transcript = alternative.get("transcript", "")
                    words = alternative.get("words", [])
                    new_word_cnt = len(words) - len(running_words)
                    new_words: list[str] = []
                    if new_word_cnt > 0:
                        new_words = [w["word"] for w in words[:new_word_cnt]]
                        running_words.extend(new_words)

                    self._output_queue.put_nowait(
                        STTEvent_Transcription(
                            trans_id,
                            delta_text=" ".join(new_words),
                            running_text=transcript,
                        )
                    )

                    if len(words) > 0:
                        end_ms = words[-1]["end"] * 1000.0
                        if start_ms < 0:
                            start_ms = words[0]["start"] * 1000.0

                    if is_final:
                        commit_transcription()

                elif msg_type == "SpeechStarted":
                    if start_ms < 0:
                        start_ms = data.get("timestamp", 0) * 1000
                        self._output_queue.put_nowait(
                            STTEvent_SpeechStarted(id=trans_id)
                        )
                elif msg_type == "UtteranceEnd":
                    last_word: float = data["last_word"]
                    end_ms = last_word * 1000.0
                    commit_transcription()
                else:
                    logging.warning("Deepgram Unknown message type: %s", msg)

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

        config = {
            "model": "nova-3-general",
            "punctuate": True,
            "smart_format": True,
            "encoding": "linear16",
            "sample_rate": 24000,
            "channels": 1,
            "filler_words": True,
            "interim_results": True,
            "utterance_end_ms": "1000",
            "vad_events": True,
            "endpointing": 750,
        }
        url = f"wss://api.deepgram.com/v1/listen?{urlencode(config).lower()}"

        async with aiohttp.ClientSession(
            headers={"Authorization": f"Token {self._api_key}"}
        ) as session:
            async with session.ws_connect(url) as ws:
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
