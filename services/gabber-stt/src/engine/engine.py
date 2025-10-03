import asyncio
import logging
from dataclasses import dataclass

import numpy as np
from lib import eot, resampler, stt, vad
from enum import Enum

logger = logging.getLogger(__name__)


class Engine:
    def __init__(
        self,
        *,
        input_sample_rate: int,
        eot: eot.EndOfTurn,
        vad: vad.VAD,
        stt: stt.STT,
    ):
        self._input_sample_rate = input_sample_rate
        self._eot = eot
        self._vad = vad
        self._stt = stt
        self.vad_session = self._vad.create_session()
        self._resamplers: dict[int, resampler.Resampler] = {}
        self.audio_window = AudioWindow(max_length_s=60.0)
        self.setup_resamplers()
        self._tasks = []
        self.current_state: BaseEngineState = EngineState_NotTalking(engine=self)

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
    def __init__(self, *, engine: "Engine"):
        self.name = self.__class__.__name__.split("_")[-1]
        self.engine = engine

    async def tick(self): ...


class EngineState_NotTalking(BaseEngineState):
    def __init__(self, *, engine: "Engine", vad_threshold: float = 0.4):
        super().__init__(engine=engine)
        self._last_inference_cursor = self.engine.audio_window._end_cursors.get(
            self.engine._input_sample_rate, 0
        )

    async def tick(self):
        current_curs = self.engine.audio_window._end_cursors.get(
            self.engine._input_sample_rate, 0
        )

        for i in range(
            self._last_inference_cursor,
            current_curs,
            self.engine.vad_session.chunk_size,
        ):
            end_cursor = min(i + self.engine.vad_session.chunk_size, current_curs)
            if end_cursor - i != self.engine.vad_session.chunk_size:
                break
            segment = self.engine.audio_window.get_segment(
                sample_rate=self.engine._input_sample_rate,
                start_cursor=i,
                end_cursor=end_cursor,
            )
            res = await self.engine.vad_session.has_voice(segment)
            print(f"NEIL VAD result: {res}")
            self._last_inference_cursor = end_cursor


class EngineState_TalkingWarmUp(BaseEngineState):
    def __init__(self, *, engine: "Engine", start_cursor: int):
        super().__init__(engine=engine)


class EngineState_Talking(BaseEngineState):
    def __init__(self, *, engine: "Engine"):
        super().__init__(engine=engine)


class EngineState_TalkingCoolDown(BaseEngineState):
    def __init__(self, *, engine: "Engine"):
        super().__init__(engine=engine)


class EngineState_Finalizing(BaseEngineState):
    def __init__(self, *, engine: "Engine"):
        super().__init__(engine=engine)


class EngineState_FinalizingInterrupting(BaseEngineState):
    def __init__(self, *, engine: "Engine"):
        super().__init__(engine=engine)


class EngineState_Finalized(BaseEngineState):
    def __init__(self, *, engine: "Engine"):
        super().__init__(engine=engine)
