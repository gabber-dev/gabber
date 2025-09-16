# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import base64
from typing import Any

from gabber.utils import ItalicRemover, ParenthesisRemover, EmojiRemover

from .tts import MultiplexWebSocketTTS

SAMPLE_RATE = 24000
CHANNELS = 1


class GabberTTS(MultiplexWebSocketTTS):
    def __init__(self, *, api_key: str):
        super().__init__()
        self._api_key = api_key
        self._emoji_remover = EmojiRemover()
        self._italic_remover = ItalicRemover()
        self._parenthesis_remover = ParenthesisRemover()

    def start_session_payload(self, *, context_id: str, voice: str) -> dict[str, Any]:
        return {
            "type": "start_session",
            "payload": {
                "voice": voice,
            },
            "session": context_id,
        }

    def push_text_payload(
        self, *, text: str, context_id: str, voice: str
    ) -> dict[str, Any]:
        text = self._emoji_remover.push_text(text)
        text = self._parenthesis_remover.push_text(text)
        text = self._italic_remover.push_text(text)
        return {
            "type": "push_text",
            "session": context_id,
            "payload": {
                "text": text,
            },
        }

    def eos_payloads(self, *, context_id: str, voice: str) -> list[dict[str, Any]]:
        return [
            {
                "type": "eos",
                "session": context_id,
                "voice": voice,
            }
        ]

    def get_context_id(self, msg: dict[str, Any]) -> str:
        return msg["session"]

    def get_pcm_bytes(self, msg: dict[str, Any]) -> bytes:
        b64 = msg["payload"]["audio"]
        audio_bytes = base64.b64decode(b64)
        return audio_bytes

    def get_error_message(self, msg: dict[str, Any]) -> str:
        return msg["payload"]["message"]

    def is_audio_message(self, msg: dict[str, Any]) -> bool:
        return msg["type"] == "audio"

    def is_final_message(self, msg: dict[str, Any]) -> bool:
        return msg["type"] == "final"

    def is_error_message(self, msg: dict[str, Any]) -> bool:
        return msg["type"] == "error"

    def get_url(self) -> str:
        # return f"wss://api.gabber.dev/voice/websocket?api-key={self._api_key}"
        return f"wss://api.gabber.dev/voice/websocket?api-key={self._api_key}"

    def get_headers(self) -> dict[str, str]:
        return {}
