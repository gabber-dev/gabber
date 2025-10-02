from .stt import STT


class CanarySTT(STT):
    @property
    def sample_rate(self) -> int:
        return 16000
