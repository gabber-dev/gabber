from core import (
    AudioInference,
    AudioInferenceEngine,
)
from enum import Enum
from dataclasses import dataclass


class Viseme(Enum):
    SILENCE = 0
    PP = 1
    FF = 2
    TH = 3
    DD = 4
    kk = 5
    CH = 6
    SS = 7
    nn = 8
    RR = 9
    aa = 10
    E = 11
    ih = 12
    oh = 13
    ou = 14


class LipSyncInference(AudioInference["list[LipSyncResult]"]): ...


class LipSyncInferenceEngine(AudioInferenceEngine["list[LipSyncResult]"]): ...


@dataclass
class VisemeProability:
    viseme: Viseme
    probability: float


@dataclass
class LipSyncResult:
    max_viseme_prob: VisemeProability
    start_sample: int
    end_sample: int
