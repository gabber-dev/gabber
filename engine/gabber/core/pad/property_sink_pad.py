# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import TYPE_CHECKING, Literal, Generic, TypeVar

from .pad import Item, PropertyPad, SinkPad, SourcePad, NOTIFIABLE_TYPES
from ..types import pad_constraints, runtime

if TYPE_CHECKING:
    from ..node import Node

PROPERTY_SINK_PAD_T = TypeVar("PROPERTY_SINK_PAD_T", bound=runtime.RuntimePadValue)


class PropertySinkPad(
    SinkPad[PROPERTY_SINK_PAD_T],
    PropertyPad[PROPERTY_SINK_PAD_T],
    Generic[PROPERTY_SINK_PAD_T],
):
    def __init__(
        self,
        *,
        id: str,
        group: str,
        owner_node: "Node",
        value: PROPERTY_SINK_PAD_T,
        default_type_constraints: list[pad_constraints.BasePadType] | None = None,
    ):
        super().__init__()
        self._id = id
        self._group = group
        self._owner_node = owner_node
        self._type_constraints = default_type_constraints
        self._default_type_constraints = default_type_constraints
        self._value = value
        self._previous_pad: SourcePad | None = None
        self._queue = asyncio.Queue[Item | None]()

    def get_id(self) -> str:
        return self._id

    def set_id(self, id: str) -> None:
        self._id = id

    def get_group(self) -> str:
        return self._group

    def get_owner_node(self) -> "Node":
        return self._owner_node

    def get_type_constraints(self):
        return self._type_constraints

    def set_type_constraints(
        self, constraints: list[pad_constraints.BasePadType] | None
    ) -> None:
        self._type_constraints = constraints

    def set_default_type_constraints(
        self, constraints: list[pad_constraints.BasePadType] | None
    ) -> None:
        self._default_type_constraints = constraints
        self._resolve_type_constraints()

    def get_default_type_constraints(self):
        return self._default_type_constraints

    def get_previous_pad(self) -> SourcePad | None:
        return self._previous_pad

    def set_previous_pad(self, pad: SourcePad | None) -> None:
        self._previous_pad = pad

    def get_editor_type(self) -> str:
        return "PropertySinkPad"

    def get_direction(self) -> Literal["source"] | Literal["sink"]:
        return "sink"

    def get_value(self) -> PROPERTY_SINK_PAD_T:
        return self._value

    def set_value(self, value: PROPERTY_SINK_PAD_T):
        self._value = value
        if isinstance(value, NOTIFIABLE_TYPES):
            self._notify_update(value)

    def _get_queue(self) -> asyncio.Queue[Item | None]:
        return self._queue

    def __aiter__(self) -> SinkPad:
        return self

    async def __anext__(self) -> Item:
        res = await self._queue.get()
        if res is None:
            raise StopAsyncIteration
        return res
