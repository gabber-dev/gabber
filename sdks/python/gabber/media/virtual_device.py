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

from .media_iterator import MediaIterator
from typing import Generic, TypeVar

T = TypeVar("T")


class VirtualDevice(Generic[T]):
    def __init__(self):
        self._iterators: list[MediaIterator[T]] = []

    def push(self, item: T):
        for iterator in self._iterators:
            iterator._push(item)

    def _close(self):
        for iterator in self._iterators:
            iterator._eos()

    def create_iterator(self):
        iterator = MediaIterator[T](owner=self)
        self._iterators.append(iterator)
        return iterator

    def remove_iterator(self, iterator: MediaIterator[T]):
        self._iterators.remove(iterator)
