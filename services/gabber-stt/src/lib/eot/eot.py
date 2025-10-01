from typing import Protocol


class EndOfTurn(Protocol):
    @property
    def sample_rate(self) -> int: ...
