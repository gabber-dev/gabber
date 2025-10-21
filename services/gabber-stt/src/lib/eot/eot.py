from core import (
    AudioInferenceEngine,
    AudioInference,
)


class EndOfTurnEngine(AudioInferenceEngine[float]): ...


class EOTInference(AudioInference[float]): ...
