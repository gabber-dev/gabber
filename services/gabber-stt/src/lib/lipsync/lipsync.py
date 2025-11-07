from core import (
    AudioInference,
    AudioInferenceEngine,
)
from enum import Enum
from dataclasses import dataclass


class Viseme(Enum):
    SILENCE = "SILENCE"
    PP = "PP"
    FF = "FF"
    TH = "TH"
    DD = "DD"
    KK = "KK"
    CH = "CH"
    SS = "SS"
    NN = "NN"
    RR = "RR"
    AA = "AA"
    E = "E"
    IH = "IH"
    OH = "OH"
    OU = "OU"


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
