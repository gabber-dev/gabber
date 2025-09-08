"""
* Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*
* SPDX-License-Identifier: Apache-2.0
"""

from typing import Callable, Generic, TypeVar, cast

from livekit import rtc

from .engine import Engine
from .types import PadValue
from generated import runtime

DataType = TypeVar("DataType", bound=PadValue)


class BasePad(Generic[DataType]):
    def __init__(
        self, *, engine: Engine, node_id: str, pad_id: str, livekit_room: rtc.Room
    ):
        self.engine: Engine = engine
        self._node_id: str = node_id
        self._pad_id: str = pad_id
        self.livekit_room: rtc.Room = livekit_room
        self.handlers: list[Callable[[DataType], None]] = []
        self.engine._add_pad_value_handler(
            self.node_id, self.pad_id, self.on_pad_value_event
        )

    def on(self, event: str, handler: Callable[[DataType], None]) -> None:
        if event == "value":
            self.handlers.append(handler)

    def off(self, event: str, handler: Callable[[DataType], None]) -> None:
        if event == "value":
            self.handlers = [h for h in self.handlers if h != handler]

    def destroy(self) -> None:
        self.handlers = []
        self.engine._remove_pad_value_handler(
            self.node_id, self.pad_id, self.on_pad_value_event
        )

    def on_pad_value_event(self, value: PadValue) -> None:
        for handler in self.handlers:
            handler(cast(DataType, value))

    @property
    def node_id(self) -> str:
        return self._node_id

    @node_id.setter
    def node_id(self, value: str) -> None:
        self._node_id = value

    @property
    def pad_id(self) -> str:
        return self._pad_id

    @pad_id.setter
    def pad_id(self, value: str) -> None:
        self._pad_id = value

    async def _get_value(self) -> PadValue:
        resp = await self.engine.runtime_request(
            runtime.RuntimeRequestPayloadGetValue(
                type="get_value", node_id=self.node_id, pad_id=self.pad_id
            )
        )
        if resp.type != "get_value":
            raise ValueError(f"Unexpected response type: {resp.type}")

        return resp.value


class SourcePad(BasePad[DataType]):
    def __init__(
        self, *, engine: Engine, node_id: str, pad_id: str, livekit_room: rtc.Room
    ):
        super().__init__(
            engine=engine, node_id=node_id, pad_id=pad_id, livekit_room=livekit_room
        )

    async def push_value(self, value: DataType) -> None:
        await self.engine.runtime_request(
            runtime.RuntimeRequestPayloadPushValue(
                value=value,
                node_id=self.node_id,
                pad_id=self.pad_id,
                type="push_value",
            )
        )


class SinkPad(BasePad[DataType]):
    def __init__(
        self, *, engine: Engine, node_id: str, pad_id: str, livekit_room: rtc.Room
    ):
        super().__init__(
            engine=engine, node_id=node_id, pad_id=pad_id, livekit_room=livekit_room
        )


class PropertyPad(BasePad[DataType]):
    def __init__(
        self, *, engine: Engine, node_id: str, pad_id: str, livekit_room: rtc.Room
    ):
        super().__init__(
            engine=engine, node_id=node_id, pad_id=pad_id, livekit_room=livekit_room
        )

    async def get_value(self) -> "PadValue":
        return await self._get_value()
