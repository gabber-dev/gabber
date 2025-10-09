import asyncio
import logging
import time
import wave
from dataclasses import dataclass
from typing import Callable

import numpy as np
from core import AudioWindow
from lib import eot, stt, vad
from utils import ExponentialMovingAverage

logger = logging.getLogger(__name__)


@dataclass
class EngineSettings:
    vad_threshold: float = 0.4
    speaking_started_warmup_time_s: float = 0.25
    vad_cooldown_time_s: float = 1.0


class Engine:
    def __init__(
        self,
        *,
        input_sample_rate: int,
        eot: eot.EndOfTurnEngine,
        vad: vad.VADInferenceEngine,
        stt: stt.STTInferenceEngine,
        settings: EngineSettings = EngineSettings(),
    ):
        self._input_sample_rate = input_sample_rate
        self._eot = eot
        self._vad = vad
        self._stt = stt
        self.vad_session = self._vad.create_session()
        self.eot_session = self._eot.create_session()
        self.stt_session = self._stt.create_session()
        self.audio_window = AudioWindow(
            max_length_s=10.0,
            sample_rates=[
                self.vad_session.sample_rate,
                self.eot_session.sample_rate,
                self.stt_session.sample_rate,
            ],
            input_sample_rate=input_sample_rate,
        )
        self._tasks = []
        self.settings = settings
        self.current_state: BaseEngineState = EngineState_NotTalking(
            state=State(engine=self)
        )
        self._on_event: Callable[[EngineEvent], None] = lambda _: None

    def set_event_handler(self, h: "Callable[[EngineEvent], None]"):
        self._on_event = h

    def push_audio(self, audio: bytes):
        original_np_data = np.frombuffer(audio, dtype=np.int16)
        self.audio_window.push_audio(audio=original_np_data)

    async def run(self):
        while True:
            await self.current_state.tick()
            await asyncio.sleep(0.01)

    def transition_to(self, new_state: "BaseEngineState"):
        logger.info(f"Transitioning from {self.current_state.name} to {new_state.name}")
        self.current_state = new_state

    def emit_event(self, evt: "EngineEvent"):
        self._on_event(evt)


class BaseEngineState:
    def __init__(self, *, state: "State"):
        self.name = self.__class__.__name__.split("_")[-1]
        self.state = state

    async def tick(self): ...


class EngineState_NotTalking(BaseEngineState):
    async def tick(self):
        await self.state.update_vad()
        # print("NEIL last voice:", self.state.latest_voice)

        voice_time = (
            self.state.latest_voice - self.state.last_non_voice
        ) / self.state.engine.vad_session.sample_rate

        if voice_time >= self.state.engine.settings.speaking_started_warmup_time_s:
            self.state.eot_cursor = self.state.latest_voice
            self.state.stt_cursor = self.state.last_non_voice - int(
                0.25 * self.state.engine.vad_session.sample_rate
            )
            self.state.emit_start_speaking()
            self.state.engine.transition_to(EngineState_Talking(state=self.state))


class EngineState_Talking(BaseEngineState):
    async def tick(self):
        current_curs = self.state.engine.audio_window._end_cursors.get(
            self.state.engine.vad_session.sample_rate, 0
        )

        await asyncio.gather(
            self.state.update_eot(), self.state.update_vad(), self.state.update_stt()
        )

        if self.state.current_stt_result.transcription != self.state.last_interim:
            self.state.emit_interim()

        time_since_last_voice = (
            current_curs - self.state.latest_voice
        ) / self.state.engine.vad_session.sample_rate

        if (
            self.state.eot
            and time_since_last_voice >= 3.0
            or time_since_last_voice >= self.state.engine.settings.vad_cooldown_time_s
        ):
            self.state.engine.transition_to(EngineState_Finalizing(state=self.state))


class EngineState_Finalizing(BaseEngineState):
    async def tick(self):
        max_eot_vad = max(self.state.eot_cursor, self.state.vad_cursor)
        next_stt = max_eot_vad + self.state.engine.stt_session.new_audio_size * 2
        if self.state.stt_cursor < next_stt:
            await self.state.update_stt()
            return

        self.state.emit_final()
        self.state.reset()
        self.state.engine.transition_to(EngineState_NotTalking(state=self.state))


class State:
    def __init__(self, *, engine: Engine):
        self.engine = engine
        self.trans_id = 1
        self.current_stt_result = stt.STTInferenceResult(
            transcription="", words=[], start_cursor=0, end_cursor=0
        )
        self.vad_cursor = 0
        self.eot_cursor = 0
        self.stt_cursor = 0

        self.latest_voice = -1
        self.last_non_voice = 0

        self.eot = False

        self.vad_history = np.zeros(10, dtype=np.float32)
        self.bell_kernel = np.hanning(10).astype(np.float32) / np.sum(np.hanning(10))

        self.last_interim: str = ""

    async def update_vad(self):
        current_curs = self.engine.audio_window._end_cursors.get(
            self.engine.vad_session.sample_rate, 0
        )

        for i in range(
            self.vad_cursor,
            current_curs,
            self.engine.vad_session.new_audio_size,
        ):
            end_cursor = min(i + self.engine.vad_session.new_audio_size, current_curs)
            segment = self.engine.audio_window.get_segment(
                sample_rate=self.engine.vad_session.sample_rate,
                start_curs=i,
                ends_curs=end_cursor,
            )
            if segment.shape[0] < self.engine.vad_session.new_audio_size:
                break

            res = await self.engine.vad_session.inference(segment)
            self.vad_cursor = end_cursor
            self.vad_history = np.roll(self.vad_history, -1)
            self.vad_history[-1] = res
            vad_value = float(
                np.convolve(self.vad_history, self.bell_kernel, mode="valid")[0]
            )

            # print("NEIL VAD:", vad_value)

            if vad_value < self.engine.settings.vad_threshold / 3:
                self.last_non_voice = end_cursor

            if vad_value > self.engine.settings.vad_threshold:
                self.latest_voice = end_cursor

    async def update_eot(self):
        current_curs = self.engine.audio_window._end_cursors.get(
            self.engine.eot_session.sample_rate, 0
        )

        for i in range(
            self.eot_cursor,
            current_curs,
            self.engine.eot_session.new_audio_size,
        ):
            end_cursor = min(i + self.engine.eot_session.new_audio_size, current_curs)
            segment = self.engine.audio_window.get_segment(
                sample_rate=self.engine.eot_session.sample_rate,
                start_curs=i,
                ends_curs=end_cursor,
            )
            if segment.shape[0] < self.engine.eot_session.new_audio_size:
                break

            res = await self.engine.eot_session.inference(segment)
            self.eot_cursor = end_cursor
            self.eot = res >= 0.5

    async def update_stt(self):
        current_curs = self.engine.audio_window._end_cursors.get(
            self.engine.stt_session.sample_rate, 0
        )

        for i in range(
            self.stt_cursor,
            current_curs,
            self.engine.stt_session.new_audio_size,
        ):
            end_cursor = min(i + self.engine.stt_session.new_audio_size, current_curs)
            segment = self.engine.audio_window.get_segment(
                sample_rate=self.engine.stt_session.sample_rate,
                start_curs=i,
                ends_curs=end_cursor,
            )
            if segment.shape[0] < self.engine.stt_session.new_audio_size:
                break

            res = await self.engine.stt_session.inference(segment)
            self.stt_cursor = end_cursor

            # adjust cursors
            # res.start_cursor = res.start_cursor
            # res.end_cursor = res.end_cursor
            # for w in res.words:
            #     w.start_cursor = w.start_cursor
            #     w.end_cursor = w.end_cursor

            self.current_stt_result = res

    def reset(self):
        current_curs_vad = self.engine.audio_window._end_cursors.get(
            self.engine.vad_session.sample_rate, 0
        )
        current_curs_stt = self.engine.audio_window._end_cursors.get(
            self.engine.stt_session.sample_rate, 0
        )
        current_curs_eot = self.engine.audio_window._end_cursors.get(
            self.engine.eot_session.sample_rate, 0
        )
        self.vad_cursor = current_curs_vad
        self.eot_cursor = current_curs_eot
        self.stt_cursor = current_curs_stt
        self.latest_voice = -1
        self.last_non_voice = 0
        self.eot = False
        self.current_stt_result = stt.STTInferenceResult(
            transcription="", words=[], start_cursor=0, end_cursor=0
        )
        self.last_interim = ""
        self.trans_id += 1
        self.vad_history = np.zeros(10, dtype=np.float32)
        self.engine.vad_session.reset()
        self.engine.eot_session.reset()
        self.engine.stt_session.reset()

    def emit_start_speaking(self):
        self.engine.emit_event(
            EngineEvent_SpeakingStarted(
                trans_id=self.trans_id,
                start_sample=self.last_non_voice
                - int(0.25 * self.engine.vad_session.sample_rate),
            )
        )

    def emit_interim(self):
        self.engine.emit_event(
            EngineEvent_InterimTranscription(
                trans_id=self.trans_id,
                start_sample=self.current_stt_result.start_cursor,
                end_sample=self.current_stt_result.end_cursor,
                transcription=self.current_stt_result.transcription,
            )
        )
        self.last_interim = self.current_stt_result.transcription

    def emit_final(self):
        # with wave.open(f"utterance_{self.trans_id}.wav", "wb") as wf:
        #     wf.setnchannels(1)
        #     wf.setsampwidth(2)
        #     wf.setframerate(self.engine.stt_session.sample_rate)
        #     audio_data = self.engine.audio_window.get_segment(
        #         sample_rate=self.engine.stt_session.sample_rate,
        #         start_cursor=self.first_voice,
        #         end_cursor=self.stt_cursor,
        #     )
        #     wf.writeframes(audio_data.tobytes())

        self.engine.emit_event(
            EngineEvent_FinalTranscription(
                trans_id=self.trans_id,
                start_sample=self.current_stt_result.start_cursor,
                end_sample=self.current_stt_result.end_cursor,
                transcription=self.current_stt_result.transcription,
            )
        )


@dataclass
class EngineEvent_Error:
    message: str


@dataclass
class EngineEvent_InterimTranscription:
    trans_id: int
    start_sample: int
    end_sample: int
    transcription: str


@dataclass
class EngineEvent_SpeakingStarted:
    trans_id: int
    start_sample: int


@dataclass
class EngineEvent_FinalTranscription:
    trans_id: int
    transcription: str
    start_sample: int
    end_sample: int


EngineEvent = (
    EngineEvent_Error
    | EngineEvent_FinalTranscription
    | EngineEvent_InterimTranscription
    | EngineEvent_SpeakingStarted
)
