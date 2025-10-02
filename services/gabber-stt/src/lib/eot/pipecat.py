from .eot import EndOfTurn


class PipeCatEOT(EndOfTurn):
    @property
    def sample_rate(self) -> int:
        return 16000
