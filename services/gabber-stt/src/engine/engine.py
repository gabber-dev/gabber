from dataclasses import dataclass

import numpy as np
from lib import eot, resampler, stt, vad


class Engine:
    def __init__(
        self,
        *,
        sample_rate: int,
        eot: eot.EndOfTurn,
        vad: vad.VADInference,
        stt: stt.STT,
    ):
        self._sample_rate = sample_rate
        self._eot = eot
        self._vad = vad
        self._stt = stt
        self._resamplers: dict[int, resampler.Resampler] = {}
        self._audio_window = AudioWindow(max_length_s=60.0)

    def setup_resamplers(self):
        sample_rates = {
            self._eot.sample_rate,
            self._vad.sample_rate,
            self._stt.sample_rate,
        }
        for rate in sample_rates:
            if rate != self._sample_rate and rate not in self._resamplers:
                self._resamplers[rate] = resampler.Resampler(
                    input_rate=self._sample_rate, output_rate=rate
                )

    def push_audio(self, audio: bytes):
        original_np_data = np.frombuffer(audio, dtype=np.int16)
        original_data = AudioData(sample_rate=self._sample_rate, data=original_np_data)
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
        self._max_length_s = max_length_s

    def push_frame(self, frame: AudioFrame):
        if frame.original_data.sample_rate not in self._data:
            self._data[frame.original_data.sample_rate] = np.array([], dtype=np.int16)
            self._start_cursors[frame.original_data.sample_rate] = 0

        self._data[frame.original_data.sample_rate] = np.concatenate(
            self._data[frame.original_data.sample_rate], frame.original_data.data
        )

        for rate in frame.resampled_data:
            if rate not in self._data:
                self._data[rate] = np.array([], dtype=np.int16)
                self._start_cursors[rate] = 0

            existing = self._data[rate]
            new_data = frame.resampled_data[rate].data
            concatted: np.typing.NDArray[np.int16] = np.concatenate(
                (existing, new_data)
            )
            self._data[rate] = concatted

        self.prune_if_necessary()

    def prune_if_necessary(self):
        for rate in self._data:
            max_length_samples = int(self._max_length_s * rate)
            # Prune when we have more than double the max length
            # to avoid excessive copying
            if len(self._data[rate]) > max_length_samples * 2:
                self._data[rate] = self._data[rate][-max_length_samples:]
                self._start_cursors[rate] = max(
                    0, len(self._data[rate]) - max_length_samples
                )
