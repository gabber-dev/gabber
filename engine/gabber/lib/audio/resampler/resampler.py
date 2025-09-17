# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import av
import numpy as np
from gabber.core import runtime_types


class Resampler:
    def __init__(self, output_rate):
        self._output_rate = output_rate
        self._resampler = av.AudioResampler(
            format="s16",
            layout="mono",
            rate=output_rate,
        )

    def push_audio(
        self, frame_data: runtime_types.AudioFrameData
    ) -> runtime_types.AudioFrameData:
        if frame_data.sample_rate == self._output_rate:
            return frame_data
        f = av.AudioFrame.from_ndarray(
            frame_data.data,
            format="s16",
            layout="mono",
        )
        f.sample_rate = frame_data.sample_rate
        frames = self._resampler.resample(f)
        concatted_frames = np.concatenate(
            [np.frombuffer(frame.to_ndarray(), dtype=np.int16) for frame in frames]
        )
        return runtime_types.AudioFrameData(
            data=concatted_frames.reshape(1, -1),
            sample_rate=self._output_rate,
            num_channels=1,
        )

    def eos(self) -> runtime_types.AudioFrameData:
        frames = self._resampler.resample(None)
        concatted_frames = np.concatenate(
            [np.frombuffer(frame.to_ndarray(), dtype=np.int16) for frame in frames]
        )
        return runtime_types.AudioFrameData(
            data=concatted_frames.reshape(1, -1),
            sample_rate=self._output_rate,
            num_channels=1,
        )
