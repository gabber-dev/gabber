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

import asyncio
from typing import Generic, TypeVar, Protocol
from weakref import ref

T = TypeVar("T")


class MediaIteratorOwner(Protocol):
    def remove_iterator(self, iterator: "MediaIterator"): ...


class MediaIterator(Generic[T]):
    def __init__(self, *, owner: MediaIteratorOwner):
        self._q = asyncio.Queue[T | None]()
        self._owner = ref(owner)

    def _push(self, item: T):
        self._q.put_nowait(item)

    def _eos(self):
        self._q.put_nowait(None)

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self._q.get()
        if item is None:
            raise StopAsyncIteration
        return item

    def cleanup(self):
        while not self._q.empty():
            self._q.get_nowait()
        self._q.put_nowait(None)

        owner = self._owner()
        if owner is not None:
            owner.remove_iterator(self)
