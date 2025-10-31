import asyncio
import logging
from dataclasses import dataclass
from typing import Callable, TypeVar

import numpy as np
from core import AudioWindow
from lib import eot, lipsync, stt, vad

from .lipsync_state import (
    BaseLipSyncState,
    LipSyncEvent_Viseme,
    LipSyncState_Listening,
    ListeningState,
)
from .stt_state import (
    BaseSTTState,
    NotTalkingState,
    STTEvent_FinalTranscription,
    STTEvent_InterimTranscription,
    STTEvent_SpeakingStarted,
    STTState_NotTalking,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class EngineSettings:
    initial_vad_threshold: float = 0.5
    vad_sustained_threshold: float = 0.25
    speaking_started_warmup_time_s: float = 0.1
    vad_cooldown_time_s: float = 0.5
    eot_timeout_s: float = 1.5
    lipsync_delay_s: float = 0.25
    lipsync_enabled: bool = False
    stt_enabled: bool = True


class Engine:
    def __init__(
        self,
        *,
        input_sample_rate: int,
        eot: eot.EndOfTurnEngine,
        vad: vad.VADInferenceEngine,
        stt: stt.STTInferenceEngine,
        lipsync: lipsync.LipSyncInferenceEngine,
        settings: EngineSettings = EngineSettings(),
    ):
        self._input_sample_rate = input_sample_rate
        self.eot = eot
        self.vad = vad
        self.stt = stt
        self.lipsync = lipsync
        self.audio_window = AudioWindow(
            max_length_s=60.0,
            sample_rates=[
                self.vad.sample_rate,
                self.stt.sample_rate,
                self.eot.sample_rate,
                self.lipsync.sample_rate,
            ],
            input_sample_rate=input_sample_rate,
        )
        self._tasks = []
        self.settings = settings
        self.stt_state: BaseSTTState = STTState_NotTalking(
            engine=self, state=NotTalkingState(vad_cursor=0)
        )
        self.lipsync_state: BaseLipSyncState = LipSyncState_Listening(
            engine=self, state=ListeningState()
        )
        self._on_event: Callable[[EngineEvent], None] = lambda _: None

    def set_event_handler(self, h: "Callable[[EngineEvent], None]"):
        self._on_event = h

    def push_audio(self, audio: bytes):
        original_np_data = np.frombuffer(audio, dtype=np.int16)
        self.audio_window.push_audio(audio=original_np_data)

    async def run(self):
        while True:
            fns = []

            if self.settings.stt_enabled:
                fns.append(self.stt_state.tick)

            if self.settings.lipsync_enabled:
                fns.append(self.lipsync_state.tick)

            await asyncio.gather(*(fn() for fn in fns))
            await asyncio.sleep(0.01)

    def transition_to(self, new_state: "BaseSTTState[T]"):
        logger.info(f"Transitioning from {self.stt_state.name} to {new_state.name}")
        self.stt_state = new_state

    def emit_event(self, evt: "EngineEvent"):
        self._on_event(evt)


EngineEvent = (
    STTEvent_FinalTranscription
    | STTEvent_InterimTranscription
    | STTEvent_SpeakingStarted
    | LipSyncEvent_Viseme
)
