import numpy as np
from .resampler import Resampler


class AudioWindow:
    def __init__(
        self, *, max_length_s: float, sample_rates: list[int], input_sample_rate: int
    ):
        self._input_sample_rate = input_sample_rate
        self._sample_rates = sample_rates
        self._data: dict[int, np.typing.NDArray[np.int16]] = {}
        self._start_cursors: dict[int, int] = {}
        self._end_cursors: dict[int, int] = {}
        self._max_length_s = max_length_s
        self._resamplers: dict[int, Resampler] = {}
        self._setup_resamplers()

    def _setup_resamplers(self):
        for rate in self._sample_rates:
            if rate != self._input_sample_rate and rate not in self._resamplers:
                self._resamplers[rate] = Resampler(
                    input_rate=self._input_sample_rate, output_rate=rate
                )

    def push_audio(self, *, audio: np.typing.NDArray[np.int16]):
        for rate in self._sample_rates:
            if rate == self._input_sample_rate:
                resampled_data = audio
            else:
                resampled_data = self._resamplers[rate].push_audio(audio)

            if rate not in self._data:
                self._data[rate] = np.array([], dtype=np.int16)
                self._start_cursors[rate] = 0
                self._end_cursors[rate] = 0

            existing = self._data[rate]
            concatted: np.typing.NDArray[np.int16] = np.concatenate(
                (existing, resampled_data)
            )
            self._data[rate] = concatted
            self._end_cursors[rate] += len(resampled_data)

        self.prune_if_necessary()

    def prune_if_necessary(self):
        for rate in self._data:
            max_length_samples = int(self._max_length_s * rate)
            # Prune when we have more than double the max length
            # to avoid excessive copying
            if len(self._data[rate]) >= max_length_samples * 2:
                print("NEIL pruning audio window")
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
