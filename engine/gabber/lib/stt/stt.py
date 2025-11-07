# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from abc import ABC
from dataclasses import dataclass

from gabber.core.types.runtime import AudioClip, AudioFrame


class STT(ABC):
    def push_audio(self, audio: AudioFrame) -> None:
        """
        Push audio data to the STT engine.
        :param audio: Audio data in bytes.
        """
        pass

    def eos(self) -> None:
        """
        Signal the end of the audio stream.
        """
        pass

    def close(self) -> None:
        """
        Close the STT engine.
        """
        pass

    def __aiter__(self):
        return self

    async def __anext__(self) -> "STTEvent":
        raise StopAsyncIteration

    async def run(self) -> None:
        """
        Run the STT engine processing loop.
        """
        pass


@dataclass
class STTEvent:
    id: str


@dataclass
class STTEvent_SpeechStarted(STTEvent):
    pass


@dataclass
class STTEvent_Transcription(STTEvent):
    delta_text: str
    running_text: str


@dataclass
class STTEvent_EndOfTurn(STTEvent):
    clip: AudioClip


@dataclass
class STTEvent_Viseme(STTEvent):
    viseme: str
