import asyncio
import logging
import time
import wave
from dataclasses import dataclass
from typing import Callable

import numpy as np
from lib import eot, resampler, stt, vad
from utils import ExponentialMovingAverage

logger = logging.getLogger(__name__)


@dataclass
class EngineSettings:
    vad_threshold: float = 0.4
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
        self._resamplers: dict[int, resampler.Resampler] = {}
        self.audio_window = AudioWindow(max_length_s=60.0)
        self.setup_resamplers()
        self._tasks = []
        self.settings = settings
        self.current_state: BaseEngineState = EngineState_NotTalking(
            state=State(engine=self)
        )
        self._on_event: Callable[[EngineEvent], None] = lambda _: None

    def set_event_handler(self, h: "Callable[[EngineEvent], None]"):
        self._on_event = h

    def setup_resamplers(self):
        sample_rates = {
            self._eot.sample_rate,
            self._vad.sample_rate,
            self._stt.sample_rate,
        }
        for rate in sample_rates:
            if rate != self._input_sample_rate and rate not in self._resamplers:
                self._resamplers[rate] = resampler.Resampler(
                    input_rate=self._input_sample_rate, output_rate=rate
                )

    def push_audio(self, audio: bytes):
        original_np_data = np.frombuffer(audio, dtype=np.int16)
        original_data = AudioData(
            sample_rate=self._input_sample_rate, data=original_np_data
        )
        frame = AudioFrame(
            original_data=original_data,
            resampled_data={},
        )
        for rate in self._resamplers:
            r = self._resamplers[rate]
            resampled_np_data = r.push_audio(original_np_data)
            frame.resampled_data[rate] = AudioData(
                sample_rate=rate, data=resampled_np_data
            )
        self.audio_window.push_frame(frame)

    async def run(self):
        while True:
            await self.current_state.tick()
            await asyncio.sleep(0.01)

    def transition_to(self, new_state: "BaseEngineState"):
        logger.info(f"Transitioning from {self.current_state.name} to {new_state.name}")
        self.current_state = new_state

    def emit_event(self, evt: "EngineEvent"):
        self._on_event(evt)


@dataclass
class AudioData:
    sample_rate: int
    data: np.typing.NDArray[np.int16]


@dataclass
class AudioFrame:
    original_data: AudioData
    resampled_data: dict[int, AudioData]


class AudioWindow:
    def __init__(self, *, max_length_s: float):
        self._data: dict[int, np.typing.NDArray[np.int16]] = {}
        self._start_cursors: dict[int, int] = {}
        self._end_cursors: dict[int, int] = {}
        self._max_length_s = max_length_s

    def push_frame(self, frame: AudioFrame):
        if frame.original_data.sample_rate not in self._data:
            self._data[frame.original_data.sample_rate] = np.array((0,), dtype=np.int16)
            self._start_cursors[frame.original_data.sample_rate] = 0
            self._end_cursors[frame.original_data.sample_rate] = 0

        self._data[frame.original_data.sample_rate] = np.concatenate(
            (self._data[frame.original_data.sample_rate], frame.original_data.data)
        )
        self._end_cursors[frame.original_data.sample_rate] += len(
            frame.original_data.data
        )

        for rate in frame.resampled_data:
            if rate not in self._data:
                self._data[rate] = np.array([], dtype=np.int16)
                self._start_cursors[rate] = 0
                self._end_cursors[rate] = 0

            existing = self._data[rate]
            new_data = frame.resampled_data[rate].data
            concatted: np.typing.NDArray[np.int16] = np.concatenate(
                (existing, new_data)
            )
            self._data[rate] = concatted
            self._end_cursors[rate] += len(new_data)

        self.prune_if_necessary()

    def prune_if_necessary(self):
        for rate in self._data:
            max_length_samples = int(self._max_length_s * rate)
            # Prune when we have more than double the max length
            # to avoid excessive copying
            if len(self._data[rate]) >= max_length_samples * 2:
                old_len = len(self._data[rate])
                self._data[rate] = self._data[rate][-max_length_samples:]
                new_len = len(self._data[rate])
                delta_cursor = self._start_cursors[rate]
                self._start_cursors[rate] += old_len - new_len
                delta_cursor -= self._start_cursors[rate]

    def get_segment(
        self, *, sample_rate: int, start_cursor: int, end_cursor: int
    ) -> np.typing.NDArray[np.int16]:
        if sample_rate not in self._data:
            raise ValueError(f"Sample rate {sample_rate} not found in audio window")

        if start_cursor < self._start_cursors[sample_rate]:
            start_cursor = self._start_cursors[sample_rate]

        if end_cursor > self._end_cursors[sample_rate]:
            end_cursor = self._end_cursors[sample_rate]

        if start_cursor >= end_cursor:
            raise ValueError(f"Invalid segment: {start_cursor} >= {end_cursor}")

        start_index = start_cursor - self._start_cursors[sample_rate]
        end_index = end_cursor - self._start_cursors[sample_rate]
        return self._data[sample_rate][start_index:end_index]


class BaseEngineState:
    def __init__(self, *, state: "State"):
        self.name = self.__class__.__name__.split("_")[-1]
        self.state = state

    async def tick(self): ...


class EngineState_NotTalking(BaseEngineState):
    async def tick(self):
        await self.state.update_vad()
        if self.state.latest_voice > 0:
            self.state.eot_cursor = self.state.first_voice
            self.state.stt_cursor = self.state.first_voice
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
            and time_since_last_voice >= 0.25
            or time_since_last_voice >= self.state.engine.settings.vad_cooldown_time_s
        ):
            self.state.engine.transition_to(EngineState_Finalizing(state=self.state))


class EngineState_Finalizing(BaseEngineState):
    async def tick(self):
        max_eot_vad = max(self.state.eot_cursor, self.state.vad_cursor)
        next_stt = max_eot_vad + self.state.engine.stt_session.new_audio_size * 4
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
        self.first_voice = -1

        self.eot = False
        self.vad_results_history: list[float] = []
        self.vad_exp_avg = ExponentialMovingAverage(
            attack_time=0.05,
            release_time=0.05,
            initial_value=0,
        )

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
                start_cursor=i,
                end_cursor=end_cursor,
            )
            if segment.shape[0] < self.engine.vad_session.new_audio_size:
                break

            res = await self.engine.vad_session.inference(segment)

            self.vad_cursor = end_cursor
            dt = (end_cursor - i) / self.engine.vad_session.sample_rate
            vad_value = self.vad_exp_avg.update(dt=dt, new_value=res)
            self.vad_results_history.append(vad_value)
            if len(self.vad_results_history) > 100:
                self.vad_results_history.pop(0)
            if vad_value >= self.engine.settings.vad_threshold:
                # Go back in time to find the first 3 vad results that are below threshold
                first_vad_frame = 0
                for j in range(len(self.vad_results_history) - 1, -1, -1):
                    if self.vad_results_history[j] < 0.1:
                        first_vad_frame = j
                        break

                num_vad_frames = len(self.vad_results_history) - first_vad_frame
                self.first_voice = int(
                    end_cursor
                    - self.engine.vad_session.new_audio_size * (num_vad_frames)
                ) - int(self.engine.vad_session.sample_rate * 0.25)
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
                start_cursor=i,
                end_cursor=end_cursor,
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
                start_cursor=i,
                end_cursor=end_cursor,
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
        self.first_voice = -1
        self.eot = False
        self.current_stt_result = stt.STTInferenceResult(
            transcription="", words=[], start_cursor=0, end_cursor=0
        )
        self.vad_exp_avg.value = 0
        self.last_interim = ""
        self.trans_id += 1
        self.engine.vad_session.reset()
        self.engine.eot_session.reset()
        self.engine.stt_session.reset()

    def emit_start_speaking(self):
        self.engine.emit_event(
            EngineEvent_SpeakingStarted(
                trans_id=self.trans_id, start_sample=self.first_voice
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
