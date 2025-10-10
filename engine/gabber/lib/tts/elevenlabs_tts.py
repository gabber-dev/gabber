# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
import base64
from typing import Any

from gabber.utils import ItalicRemover, ParenthesisRemover, EmojiRemover

from .tts import MultiplexWebSocketTTS

SAMPLE_RATE = 24000
CHANNELS = 1


class ElevenLabsTTS(MultiplexWebSocketTTS):
    def __init__(
        self,
        *,
        api_key: str,
        voice: str,
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        super().__init__(logger=logger)
        self._voice = voice
        self._api_key = api_key
        self._italic_remover = ItalicRemover()
        self._parenthesis_remover = ParenthesisRemover()
        self._emoji_remover = EmojiRemover()

    def start_session_payload(self, *, context_id: str, voice: str) -> dict[str, Any]:
        return {
            "text": " ",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
            },
            "context_id": context_id,
        }

    def push_text_payload(
        self, *, text: str, context_id: str, voice: str
    ) -> dict[str, Any] | None:
        text = self._emoji_remover.push_text(text)
        text = self._parenthesis_remover.push_text(text)
        text = self._italic_remover.push_text(text)

        if text.strip() == "":
            return None

        if not text.endswith(" "):
            text += " "
        return {"text": text, "context_id": context_id}

    def eos_payloads(self, *, context_id: str, voice: str) -> list[dict[str, Any]]:
        return [
            {
                "context_id": context_id,
                "text": "",
                "flush": True,
            },
            {"context_id": context_id, "close_context": True},
        ]

    def get_context_id(self, msg: dict[str, Any]) -> str | None:
        # ElevenLabs might return context_id in snake_case or camelCase
        # Also, some messages (like errors or status) may not have a context_id
        return msg.get("contextId") or msg.get("context_id")

    def get_pcm_bytes(self, msg: dict[str, Any]) -> bytes:
        b64 = msg["audio"]
        audio_bytes = base64.b64decode(b64)
        return audio_bytes

    def get_error_message(self, msg: dict[str, Any]) -> str:
        return ""

    def is_audio_message(self, msg: dict[str, Any]) -> bool:
        return "audio" in msg

    def is_final_message(self, msg: dict[str, Any]) -> bool:
        return msg.get("isFinal", False)

    def is_error_message(self, msg: dict[str, Any]) -> bool:
        return False

    def get_url(self) -> str:
        return f"wss://api.elevenlabs.io/v1/text-to-speech/{self._voice}/multi-stream-input?output_format=pcm_24000"

    def get_headers(self) -> dict[str, str]:
        return {
            "xi-api-key": self._api_key,
        }
