from typing import Protocol


class VAD(Protocol):
    pass


class VADSession(Protocol):
    pass


class VADInference(Protocol):
    @property
    def inference_sample_length(self) -> int: ...

    @property
    def sample_rate(self) -> int: ...

    def inference(self, audio_chunks: list) -> list[float]: ...
