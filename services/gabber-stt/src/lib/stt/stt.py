from core import (
    AudioInference,
    AudioInferenceEngine,
)
from dataclasses import dataclass


@dataclass
class STTInferenceResultWord:
    word: str
    start_cursor: int
    end_cursor: int


@dataclass
class STTInferenceResult:
    transcription: str
    start_cursor: int
    end_cursor: int
    words: list[STTInferenceResultWord]


class STTInferenceEngine(AudioInferenceEngine[STTInferenceResult]):
    pass


class STTInference(AudioInference[STTInferenceResult]):
    pass
