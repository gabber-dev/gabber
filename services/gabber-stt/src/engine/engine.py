import asyncio
import logging
from dataclasses import dataclass

import numpy as np
from lib import eot, resampler, stt, vad

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
        self._vad_session = self._vad.create_session()
        self._resamplers: dict[int, resampler.Resampler] = {}
        self._audio_window = AudioWindow(max_length_s=1.0)
        self.setup_resamplers()
        self._tasks = []

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

        t = asyncio.create_task(
            self._vad_session.has_voice(
                frame.resampled_data[self._vad.sample_rate].data
            )
        )
        self._tasks.append(t)
        t.add_done_callback(lambda _: self._tasks.remove(t))

        self._audio_window.push_frame(frame)


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
