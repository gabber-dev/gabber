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

from .video_frame import VideoFrame, VideoFormat
from .media_iterator import MediaIterator
from .virtual_device import VirtualDevice


class VirtualCamera(VirtualDevice[VideoFrame]):
    def __init__(self, *, format: VideoFormat, width: int, height: int) -> None:
        self.format = format
        self.width = width
        self.height = height

        self._iterators: list[MediaIterator[VideoFrame]] = []

    def push(self, item: VideoFrame):
        if item.format != self.format:
            raise ValueError(
                f"VideoFrame has format {item.format}, expected {self.format}"
            )

        if item.width != self.width or item.height != self.height:
            raise ValueError(
                f"VideoFrame has dimensions {item.width}x{item.height}, expected {self.width}x{self.height}"
            )

        super().push(item)
