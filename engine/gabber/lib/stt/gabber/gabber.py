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
    Response,
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
    def __init__(
        self,
        *,
        logger: logging.Logger | logging.LoggerAdapter,
        url: str = "ws://localhost:7004",
    ):
        self.logger = logger
        self._process_queue = asyncio.Queue[AudioFrame | None]()
        self._closed = False
        self._output_queue = asyncio.Queue[STTEvent | None]()
        self._url = url

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
        running_words: list[str] = []
        dur: float = 0
        audio_window = AudioWindow(max_dur_s=180.0)

        async def rec_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal running_words, audio_window
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
                    continue

                data = Response.model_validate_json(msg.data)
                payload = data.payload
                if payload.type == "speaking_started":
                    self.logger.info("Speech started")
                    self._output_queue.put_nowait(
                        STTEvent_SpeechStarted(id=payload.trans_id)
                    )
                elif payload.type == "interim_transcription":
                    self.logger.info(f"Interim transcription: {payload.transcription}")
                    self._output_queue.put_nowait(
                        STTEvent_Transcription(
                            id=payload.trans_id,
                            delta_text="",
                            running_text=payload.transcription,
                        )
                    )
                elif payload.type == "final_transcription":
                    self.logger.info(f"Final transcription: {payload.transcription}")
                    clip_frames: list[AudioFrame] = audio_window.get_frames(
                        payload.start_sample, payload.end_sample
                    )
                    clip = AudioClip(
                        audio=clip_frames,
                        transcription=payload.transcription,
                    )

                    self._output_queue.put_nowait(
                        STTEvent_EndOfTurn(clip=clip, id=payload.trans_id)
                    )
                self.logger.info(f"Received message: {data}")

        async def send_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal dur
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
                audio_window.push_frame(item)
                dur += item.data_16000hz.duration

                if dur > 180:
                    raise Exception("Audio chunk too long")

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

                audio_bytes = audio_bytes[(len(audio_bytes) // 3200) * 3200 :]

        async def keepalive_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            while not self._closed:
                await asyncio.sleep(2)
                if ws.closed:
                    break
                await ws.ping()

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self._url) as ws:  # Adjust port as needed
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


class AudioWindow:
    def __init__(self, *, max_dur_s: float = 60.0):
        self.frames: list[AudioFrame] = []
        self.frames_start_sample: int = 0
        self.max_dur_s = max_dur_s
        self.cur_dur = 0.0

    def get_frames(self, start_sample: int, end_sample: int) -> list[AudioFrame]:
        result: list[AudioFrame] = []
        cur_sample = self.frames_start_sample
        for f in self.frames:
            if cur_sample + f.data_16000hz.sample_count <= start_sample:
                cur_sample += f.data_16000hz.sample_count
                continue
            if cur_sample >= end_sample:
                break
            result.append(f)
            cur_sample += f.data_16000hz.sample_count
        return result

    def push_frame(self, frame: AudioFrame) -> None:
        self.frames.append(frame)
        self.cur_dur += frame.data_16000hz.duration
        self.prune()

    def prune(self):
        while self.cur_dur > self.max_dur_s and self.frames:
            f = self.frames.pop(0)
            self.cur_dur -= f.data_16000hz.duration
            self.frames_start_sample += f.data_16000hz.sample_count
            if self.cur_dur < 0:
                self.cur_dur = 0.0
