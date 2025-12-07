import logging
from .tts import SingleplexWebSocketTTS
from typing import Literal, Any
from gabber.utils import ItalicRemover, ParenthesisRemover, EmojiRemover

MinimaxModel = Literal[
    "speech-2.6-hd", "speech-2.6-turbo", "speech-02-hd", "speech-02-turbo"
]

WS_URL = "wss://api.minimax.io/ws/v1/t2a_v2"


class MinimaxTTS(SingleplexWebSocketTTS):
    def __init__(
        self,
        *,
        api_key: str,
        model: MinimaxModel,
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        self.api_key = api_key
        self.model = model
        self.logger = logger
        self._italic_remover = ItalicRemover()
        self._parenthesis_remover = ParenthesisRemover()
        self._emoji_remover = EmojiRemover()

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

    def push_text_payload(self, *, text: str, voice: str) -> dict[str, Any] | None:
        return {
            "event": "task_continue",
            "text": text,
        }

    def eos_payloads(self, *, voice: str) -> list[dict[str, Any]]:
        return [
            {
                "event": "task_finish",
            }
        ]

    def get_context_id(self, msg: dict[str, Any]) -> str | None:
        return msg.get("session_id")

    def get_pcm_bytes(self, msg: dict[str, Any]) -> bytes:
        hex_data = msg["data"]["audio"]
        audio_bytes = bytes.fromhex(hex_data)
        return audio_bytes

    def get_error_message(self, msg: dict[str, Any]) -> str:
        return ""

    def is_audio_message(self, msg: dict[str, Any]) -> bool:
        return msg.get("event") == "task_continued"

    def is_final_message(self, msg: dict[str, Any]) -> bool:
        return msg.get("isFinal", False)

    def is_error_message(self, msg: dict[str, Any]) -> bool:
        return msg.get("event") == "task_failed"

    def get_url(self) -> str:
        return WS_URL

    def get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
        }
