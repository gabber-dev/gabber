# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from livekit import rtc
from dataclasses import dataclass


@dataclass
class AudioFrame:
    data: np.typing.NDArray[np.int16]  # (1,N) array of int16 PCM audio data
    sample_rate: int
    num_channels: int

    @property
    def duration(self) -> float:
        if self.sample_rate <= 0 or self.num_channels <= 0:
            raise ValueError(
                "Sample rate and number of channels must be greater than zero."
            )
        total_samples = self.data.size  # Total elements in the array
        if total_samples == 0:
            return 0.0
        if total_samples % self.num_channels != 0:
            raise ValueError(
                "Data size must not divisible by num_channels—possible data corruption."
            )
        return float(self.data.size) / float(self.sample_rate * self.num_channels)

    def to_livekit_audio_frame(self) -> "rtc.AudioFrame":
        return rtc.AudioFrame(
            sample_rate=self.sample_rate,
            samples_per_channel=self.data.size // self.num_channels,
            num_channels=self.num_channels,
            data=self.data.tobytes(),
        )
