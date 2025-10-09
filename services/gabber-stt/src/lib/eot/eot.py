from core import (
    AudioInferenceEngine,
    AudioInference,
    AudioInferenceSession,
)


class EndOfTurnEngine(AudioInferenceEngine[float]): ...


class EOTInference(AudioInference[float]): ...


class EOTSession(AudioInferenceSession[float]): ...
