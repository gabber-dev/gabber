# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import TYPE_CHECKING, Any

from core.pad import (
    Item,
    PropertyPad,
    ProxyPad,
    SinkPad,
    SourcePad,
    types,
)
from core.pad.pad import Pad
from .pad import NOTIFIABLE_TYPES

if TYPE_CHECKING:
    from core.node import Node


class ProxyPropertySinkPad(SinkPad, PropertyPad, ProxyPad):
    def __init__(
        self,
        *,
        id: str,
        group: str,
        owner_node: "Node",
        other: SinkPad,
    ):
        self._id = id
        self._group = group
        self._owner_node = owner_node
        self._queue = asyncio.Queue[Item | None]()
        if not isinstance(other, PropertyPad):
            raise TypeError("Other pad must be a PropertyPad")
        self._other = other

    def get_other(self) -> Pad:
        return self._other

    def get_id(self) -> str:
        return self._id

    def set_id(self, id: str) -> None:
        self._id = id

    def get_group(self) -> str:
        return self._group

    def get_owner_node(self) -> "Node":
        return self._owner_node

    def get_type_constraints(self):
        return self._other.get_type_constraints()

    def set_type_constraints(self, constraints: list[types.BasePadType] | None) -> None:
        self._other.set_type_constraints(constraints)

    def get_default_type_constraints(self) -> list[types.BasePadType] | None:
        return self._other.get_default_type_constraints()

    def get_previous_pad(self) -> SourcePad | None:
        return self._other.get_previous_pad()

    def set_previous_pad(self, pad: SourcePad | None) -> None:
        self._other.set_previous_pad(pad)

    def get_editor_type(self) -> str:
        return "PropertySinkPad"

    def get_value(self) -> Any:
        return self._other.get_value()

    def _get_queue(self) -> asyncio.Queue[Item | None]:
        return self._other._get_queue()

    def set_value(self, value: Any):
        self._other.set_value(value)
        if isinstance(value, NOTIFIABLE_TYPES):
            self._notify_update(value)
