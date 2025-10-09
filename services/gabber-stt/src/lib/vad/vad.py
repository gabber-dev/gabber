from core import (
    AudioInference,
    AudioInferenceSession,
    AudioInferenceEngine,
)


class VADInference(AudioInference[float]): ...


class VADInferenceEngine(AudioInferenceEngine[float]): ...


class VADSession(AudioInferenceSession[float]): ...
