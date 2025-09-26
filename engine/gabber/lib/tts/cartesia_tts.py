# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import base64
import logging
from typing import Any

from gabber.utils import ItalicRemover, ParenthesisRemover, EmojiRemover

from .tts import MultiplexWebSocketTTS

SAMPLE_RATE = 24000
CHANNELS = 1


class CartesiaTTS(MultiplexWebSocketTTS):
    def __init__(
        self,
        *,
        api_key: str,
        model_id: str = "sonic-2",
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        super().__init__(logger=logger)
        self._model_id = model_id
        self._api_key = api_key
        self._italic_remover = ItalicRemover()
        self._parenthesis_remover = ParenthesisRemover()
        self._emoji_remover = EmojiRemover()

    def start_session_payload(
        self, *, context_id: str, voice: str
    ) -> dict[str, Any] | None:
        return None

    def push_text_payload(
        self, *, text: str, context_id: str, voice: str
    ) -> dict[str, Any]:
        text = self._emoji_remover.push_text(text)
        text = self._parenthesis_remover.push_text(text)
        text = self._italic_remover.push_text(text)
        return {
            "model_id": self._model_id,
            "max_buffer_delay_ms": 250,
            "voice": {
                "mode": "id",
                "id": voice,
            },
            "language": "en",
            "context_id": context_id,
            "output_format": {
                "container": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": SAMPLE_RATE,
            },
            "add_timestamps": False,
            "transcript": text,
            "continue": True,
        }

    def eos_payloads(self, *, context_id: str, voice: str) -> list[dict[str, Any]]:
        return [
            {
                "model_id": self._model_id,
                "voice": {
                    "mode": "id",
                    "id": voice,
                },
                "language": "en",
                "context_id": context_id,
                "output_format": {
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": SAMPLE_RATE,
                },
                "add_timestamps": False,
                "transcript": "",
                "continue": False,
            }
        ]

    def get_context_id(self, msg: dict[str, Any]) -> str:
        return msg["context_id"]

    def get_pcm_bytes(self, msg: dict[str, Any]) -> bytes:
        b64 = msg["data"]
        audio_bytes = base64.b64decode(b64)
        return audio_bytes

    def get_error_message(self, msg: dict[str, Any]) -> str:
        return msg["error"]

    def is_audio_message(self, msg: dict[str, Any]) -> bool:
        return msg["type"] == "chunk"

    def is_final_message(self, msg: dict[str, Any]) -> bool:
        return msg["type"] == "done"

    def is_error_message(self, msg: dict[str, Any]) -> bool:
        return msg["type"] == "error"

    def get_url(self) -> str:
        return "wss://api.cartesia.ai/tts/websocket?cartesia_version=2025-04-16"

    def get_headers(self) -> dict[str, str]:
        return {"X-Api-Key": self._api_key}
