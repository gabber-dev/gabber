import asyncio
import logging
from typing import Any, Literal

import aiohttp
import numpy as np
import time

from gabber.lib.audio import Resampler
from gabber.utils import EmojiRemover, ItalicRemover, ParenthesisRemover
from gabber.core.types.runtime import AudioFrame, AudioFrameData

from .tts import TTS, TTSSession

MinimaxModel = Literal[
    "speech-2.6-hd", "speech-2.6-turbo", "speech-02-hd", "speech-02-turbo"
]

WS_URL = "wss://api.minimax.io/ws/v1/t2a_v2"


class MinimaxTTS(TTS):
    def __init__(
        self,
        *,
        api_key: str,
        model: MinimaxModel,
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.logger = logger
        self._italic_remover = ItalicRemover()
        self._parenthesis_remover = ParenthesisRemover()
        self._emoji_remover = EmojiRemover()
        self._task_queue: asyncio.Queue[asyncio.Task | None] = asyncio.Queue()
        self._running_text = ""  # TODO: For now, minimax does not support context continuation well. Instead of tokenizing sentences, we will just send the full text each time.
        self._session_tasks: set[asyncio.Task] = set()

    def start_session(self, *, voice: str) -> TTSSession:
        session = TTSSession(voice=voice, logger=self.logger)
        task = asyncio.create_task(self.session_task(session))
        self._task_queue.put_nowait(task)
        self._session_tasks.add(task)
        task.add_done_callback(lambda t: self._session_tasks.discard(t))
        return session

    def start_session_payload(self, *, voice: str) -> dict[str, Any]:
        return {
            "event": "task_start",
            "model": self.model,
            "voice_setting": {
                "voice_id": voice,
                "speed": 1,
                "vol": 1,
                "pitch": 0,
                "english_normalization": False,
            },
            "audio_setting": {
                "sample_rate": 24000,
                "format": "pcm",
                "channel": 1,
            },
        }

    def get_pcm_bytes(self, msg: dict[str, Any]) -> bytes:
        hex_data = msg["data"]["audio"]
        audio_bytes = bytes.fromhex(hex_data)
        return audio_bytes

    def is_audio_message(self, msg: dict[str, Any]) -> bool:
        return msg.get("event") == "task_continued"

    def get_url(self) -> str:
        return WS_URL

    def get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
        }

    async def run(self):
        while True:
            task = await self._task_queue.get()
            if task is None:
                break
            await task

    async def session_task(self, session: "TTSSession"):
        r_16000hz = Resampler(16000)
        r_44100hz = Resampler(44100)
        r_48000hz = Resampler(48000)
        headers = self.get_headers()

        async def receive_task(ws: aiohttp.ClientWebSocketResponse):
            while True:
                msg = await ws.receive()

                # Handle different WebSocket message types
                if msg.type == aiohttp.WSMsgType.TEXT:
                    receive_item = msg.json()
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    self.logger.warning(
                        f"WebSocket closed by server - code: {msg.data}, reason: {msg.extra}"
                    )
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")
                    break
                else:
                    self.logger.warning(
                        f"Unexpected WebSocket message type: {msg.type}"
                    )
                    raise ValueError(f"Unexpected WebSocket message type: {msg.type}")

                if receive_item.get("event") == "task_finished":
                    session._output_queue.put_nowait(None)
                elif self.is_audio_message(receive_item):
                    bytes_24000 = self.get_pcm_bytes(receive_item)
                    frame_data_24000 = AudioFrameData(
                        data=np.frombuffer(bytes_24000, dtype=np.int16).reshape(1, -1),
                        sample_rate=24000,
                        num_channels=1,
                    )
                    if len(bytes_24000) == 0:
                        continue
                    frame_data_16000 = r_16000hz.push_audio(frame_data_24000)
                    frame_data_44100 = r_44100hz.push_audio(frame_data_24000)
                    frame_data_48000 = r_48000hz.push_audio(frame_data_24000)
                    frame = AudioFrame(
                        start_timestamp=time.time(),
                        original_data=frame_data_24000,
                        data_16000hz=frame_data_16000,
                        data_24000hz=frame_data_24000,
                        data_44100hz=frame_data_44100,
                        data_48000hz=frame_data_48000,
                    )
                    session._output_queue.put_nowait(frame)
                elif receive_item.get("event") == "task_failed":
                    self.logger.error(f"TTS error for session: {receive_item}")
                    session._output_queue.put_nowait(Exception("tts failed"))

        async with aiohttp.ClientSession(headers=headers) as http_session:
            try:
                ws = await http_session.ws_connect(self.get_url())
                start_msg = self.start_session_payload(voice=session.voice)
                await ws.send_json(start_msg)
                while True:
                    ack = await ws.receive_json()
                    self.logger.info(f"NEIL Session start ack: {ack}")
                    if ack.get("event") == "task_started":
                        break

                receive_t = asyncio.create_task(receive_task(ws))
                running_text = ""
                while True:
                    input_item = await session._text_queue.get()
                    if input_item is None:
                        await ws.send_json(
                            {"event": "task_continue", "text": running_text}
                        )
                        await ws.send_json({"event": "task_finish"})
                        break

                    running_text += input_item

                await receive_t
                self.logger.info("Minimax task started")
            except Exception as e:
                self.logger.error("WebSocket connection failed", exc_info=e)
                session._output_queue.put_nowait(
                    Exception("WebSocket connection failed")
                )
