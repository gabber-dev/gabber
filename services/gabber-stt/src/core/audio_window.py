import numpy as np
from .resampler import Resampler


class AudioWindow:
    def __init__(
        self, *, max_length_s: float, sample_rates: list[int], input_sample_rate: int
    ):
        self._input_sample_rate = input_sample_rate
        self._sample_rates = sample_rates
        self._data: dict[int, np.typing.NDArray[np.int16]] = {}
        self._offsets: dict[int, int] = {}
        self._end_cursors: dict[int, int] = {}
        self._max_length_s = max_length_s
        self._resamplers: dict[int, Resampler] = {}
        self._setup_resamplers()

        for rate in self._sample_rates:
            self._data[rate] = np.array([], dtype=np.int16)
            self._offsets[rate] = 0
            self._end_cursors[rate] = 0

        self._data[self._input_sample_rate] = np.array([], dtype=np.int16)
        self._offsets[self._input_sample_rate] = 0
        self._end_cursors[self._input_sample_rate] = 0

    def _setup_resamplers(self):
        for rate in self._sample_rates:
            if rate != self._input_sample_rate and rate not in self._resamplers:
                self._resamplers[rate] = Resampler(
                    input_rate=self._input_sample_rate, output_rate=rate
                )

    def push_audio(self, *, audio: np.typing.NDArray[np.int16]):
        for rate in {*self._sample_rates, self._input_sample_rate}:
            if rate == self._input_sample_rate:
                resampled_data = audio
            else:
                resampled_data = self._resamplers[rate].push_audio(audio)

            existing = self._data[rate]
            concatted: np.typing.NDArray[np.int16] = np.concatenate(
                (existing, resampled_data)
            )
            self._data[rate] = concatted
            self._end_cursors[rate] += resampled_data.shape[0]

        self.prune_if_necessary()

    @property
    def end_cursor_time(self) -> float:
        print(self._end_cursors, self._input_sample_rate)
        return (
            self._end_cursors.get(self._input_sample_rate, 0) / self._input_sample_rate
        )

    def prune_if_necessary(self):
        for rate in self._data:
            max_length_samples = int(self._max_length_s * rate)
            # Prune when we have more than double the max length
            # to avoid excessive copying
            if len(self._data[rate]) >= max_length_samples * 2:
                old_len = len(self._data[rate])
                self._data[rate] = self._data[rate][-max_length_samples:]
                new_len = len(self._data[rate])
                self._offsets[rate] += old_len - new_len

    def get_segment(
        self, *, sample_rate: int, start_curs: int, ends_curs: int
    ) -> np.typing.NDArray[np.int16]:
        if sample_rate not in self._data:
            raise ValueError(f"Sample rate {sample_rate} not found in audio window")

        if ends_curs > self._end_cursors[sample_rate]:
            ends_curs = self._end_cursors[sample_rate]

        if start_curs >= ends_curs:
            raise ValueError(f"Invalid segment: {start_curs} >= {ends_curs}")

        start_index = start_curs - self._offsets[sample_rate]
        end_index = ends_curs - self._offsets[sample_rate]
        return self._data[sample_rate][start_index:end_index]

    def clear(self):
        for rate in self._sample_rates:
            self._data[rate] = np.array([], dtype=np.int16)
            self._offsets[rate] = 0
            self._end_cursors[rate] = 0

        self._data[self._input_sample_rate] = np.array([], dtype=np.int16)
        self._offsets[self._input_sample_rate] = 0
        self._end_cursors[self._input_sample_rate] = 0

    def convert_cursor(self, *, from_rate: int, to_rate: int, cursor: int) -> int:
        if from_rate == to_rate:
            return cursor

        if from_rate not in self._data:
            raise ValueError(f"Sample rate {from_rate} not found in audio window")

        if to_rate not in self._data:
            raise ValueError(f"Sample rate {to_rate} not found in audio window")

        time_s = cursor / from_rate
        return int(time_s * to_rate)
