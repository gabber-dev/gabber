from typing import Protocol, runtime_checkable


class STT(Protocol):
    @property
    def sample_rate(self) -> int: ...
