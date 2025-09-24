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

from .audio_frame import AudioFrame
from .virtual_device import VirtualDevice


class VirtualMicrophone(VirtualDevice[AudioFrame]):
    def __init__(self, *, channels: int, sample_rate: int):
        self.channels = channels
        self.sample_rate = sample_rate
        super().__init__()

    def push(self, item: AudioFrame):
        if item.num_channels != self.channels:
            raise ValueError(
                f"AudioFrame has {item.num_channels} channels, expected {self.channels}"
            )

        if item.sample_rate != self.sample_rate:
            raise ValueError(
                f"AudioFrame has sample rate {item.sample_rate}, expected {self.sample_rate}"
            )

        super().push(item)
