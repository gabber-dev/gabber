from core import (
    AudioInference,
    AudioInferenceEngine,
)


class VADInference(AudioInference[float]): ...


class VADInferenceEngine(AudioInferenceEngine[float]): ...
