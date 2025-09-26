# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import string
from abc import ABC, abstractmethod
from typing import Any, Protocol

import aiohttp
import numpy as np
from gabber.core.runtime_types import AudioFrame, AudioFrameData
from gabber.utils import short_uuid

from gabber.lib.audio import Resampler


class TTS(Protocol):
    def start_session(self, *, voice: str) -> "TTSSession":
        """Start a new TTS session with the given voice."""
        ...

    async def run(self):
        """Run the TTS service. This should be called once."""
        ...


class MultiplexWebSocketTTS(ABC, TTS):
    def __init__(self, *, logger: logging.Logger | logging.LoggerAdapter):
        self._closed = False
        self._send_queue = asyncio.Queue[dict[str, Any] | None]()
        self._receive_queue = asyncio.Queue[dict[str, Any] | None]()
        self._session_lookup: dict[str, "TTSSession"] = {}
        self._session_tasks: set[asyncio.Task] = set()
        self.logger = logger

    async def session_task(self, session: "TTSSession"):
        self._session_lookup[session.context_id] = session
        start_msg = self.start_session_payload(
            context_id=session.context_id, voice=session.voice
        )
        if start_msg is not None:
            self._send_queue.put_nowait(start_msg)
        pending_text = ""
        is_first = True
        while True:
            try:
                send_item = await session._text_queue.get()
                if send_item is None:
                    eos_payloads = self.eos_payloads(
                        context_id=session.context_id, voice=session.voice
                    )
                    for payload in eos_payloads:
                        self._send_queue.put_nowait(payload)
                    break
                # Handle text
                text = send_item
                if is_first:
                    pending_text += text
                    words = [w.strip(string.punctuation) for w in pending_text.split()]
                    word_count = len([w for w in words if w])
                    if word_count >= 10:
                        self._send_queue.put_nowait(
                            self.push_text_payload(
                                text=pending_text,
                                context_id=session.context_id,
                                voice=session.voice,
                            )
                        )
                        pending_text = ""
                        is_first = False
                    continue
                else:
                    self._send_queue.put_nowait(
                        self.push_text_payload(
                            text=text,
                            context_id=session.context_id,
                            voice=session.voice,
                        )
                    )
            except asyncio.CancelledError:
                session._output_queue.put_nowait(Exception("Session task cancelled"))
                break

    async def run(self):
        r_16000hz = Resampler(16000)
        r_44100hz = Resampler(44100)
        r_48000hz = Resampler(48000)

        async def send_task(ws: aiohttp.ClientWebSocketResponse):
            while True:
                send_item = await self._send_queue.get()
                if send_item is None:
                    break

                try:
                    await ws.send_json(send_item)
                except aiohttp.ClientError as e:
                    logging.error("WebSocket send failed", exc_info=e)
                    for session in self._session_lookup.values():
                        session._output_queue.put_nowait(
                            Exception("WebSocket send failed")
                        )
                    break

        async def receive_task(ws: aiohttp.ClientWebSocketResponse):
            while True:
                receive_item = await ws.receive_json()

                context_id = self.get_context_id(receive_item)
                sess = self._session_lookup.get(context_id)
                if sess is None:
                    logging.warning(
                        f"Received message for unknown session: {context_id}"
                    )
                    continue

                if self.is_final_message(receive_item):
                    sess._output_queue.put_nowait(None)
                    self._session_lookup.pop(sess.context_id, None)
                elif self.is_audio_message(receive_item):
                    bytes_24000 = self.get_pcm_bytes(receive_item)
                    frame_data_24000 = AudioFrameData(
                        data=np.frombuffer(bytes_24000, dtype=np.int16).reshape(1, -1),
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
                    sess._output_queue.put_nowait(frame)
                elif self.is_error_message(receive_item):
                    self.logger.error(
                        f"TTS error for session {sess.context_id}: {self.get_error_message(receive_item)}"
                    )
                    error_message = self.get_error_message(receive_item)
                    sess._output_queue.put_nowait(Exception(error_message))
                    self._session_lookup.pop(sess.context_id, None)

        while not self._closed:
            headers = self.get_headers()
            async with aiohttp.ClientSession(headers=headers) as session:
                try:
                    ws = await session.ws_connect(self.get_url())
                    self.logger.info("Connected to WebSocket")
                    await asyncio.gather(send_task(ws), receive_task(ws))
                except Exception as e:
                    self.logger.error("WebSocket connection failed", exc_info=e)
                    for session in self._session_lookup.values():
                        session._output_queue.put_nowait(
                            Exception("WebSocket connection failed")
                        )
                for t in self._session_tasks:
                    t.cancel()
                self._session_tasks.clear()
                await asyncio.sleep(1.0)

    def __aiter__(self):
        return self

    def start_session(self, *, voice: str):
        tts_sess = TTSSession(voice=voice)
        t = asyncio.create_task(self.session_task(tts_sess))
        self._session_tasks.add(t)
        t.add_done_callback(self._session_tasks.discard)
        return tts_sess

    @abstractmethod
    def get_url(self) -> str: ...

    @abstractmethod
    def get_headers(self) -> dict[str, str]:
        """Return headers to be used in the WebSocket connection."""
        return {}

    @abstractmethod
    def start_session_payload(
        self, *, context_id: str, voice: str
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    def push_text_payload(
        self, *, context_id: str, voice: str, text: str
    ) -> dict[str, Any]: ...

    @abstractmethod
    def eos_payloads(self, *, context_id: str, voice: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_context_id(self, msg: dict[str, Any]) -> str: ...

    @abstractmethod
    def get_pcm_bytes(self, msg: dict[str, Any]) -> bytes: ...

    @abstractmethod
    def get_error_message(self, msg: dict[str, Any]) -> str: ...

    @abstractmethod
    def is_audio_message(self, msg: dict[str, Any]) -> bool: ...

    @abstractmethod
    def is_final_message(self, msg: dict[str, Any]) -> bool: ...

    @abstractmethod
    def is_error_message(self, msg: dict[str, Any]) -> bool: ...


class TTSSession:
    def __init__(self, *, voice: str):
        self.voice = voice
        self.context_id = short_uuid()
        self._text_queue = asyncio.Queue[str | None]()
        self._output_queue = asyncio.Queue[AudioFrame | Exception | None]()
        self._closed = False

    def cancel(self):
        self._text_queue.put_nowait(None)
        self._output_queue.put_nowait(None)
        self._closed = True

    def push_text(self, text: str):
        self._text_queue.put_nowait(text)

    def eos(self):
        self._text_queue.put_nowait(None)

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self._output_queue.get()
        if item is None or self._closed:
            raise StopAsyncIteration

        if isinstance(item, Exception):
            raise item

        return item
