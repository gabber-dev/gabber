# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import av
import numpy as np


class Resampler:
    def __init__(self, *, input_rate: int, output_rate: int):
        self._input_rate = input_rate
        self._output_rate = output_rate
        self._resampler = av.AudioResampler(
            format="s16",
            layout="mono",
            rate=output_rate,
        )

    def push_audio(
        self, audio: np.typing.NDArray[np.int16]
    ) -> np.typing.NDArray[np.int16]:
        f = av.AudioFrame.from_ndarray(
            audio,
            format="s16",
            layout="mono",
        )
        f.sample_rate = self._input_rate
        frames = self._resampler.resample(f)
        concatted_frames = np.concatenate(
            [np.frombuffer(frame.to_ndarray(), dtype=np.int16) for frame in frames]
        )
        return concatted_frames

    def eos(self) -> np.typing.NDArray[np.int16]:
        frames = self._resampler.resample(None)
        concatted_frames = np.concatenate(
            [np.frombuffer(frame.to_ndarray(), dtype=np.int16) for frame in frames]
        )
        return concatted_frames
