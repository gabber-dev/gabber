# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import TYPE_CHECKING

from core.pad import Item, Pad, ProxyPad, SinkPad, SourcePad, types

if TYPE_CHECKING:
    from core.node import Node


class ProxyStatelessSinkPad(SinkPad, ProxyPad):
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

    def get_previous_pad(self) -> SourcePad | None:
        return self._other.get_previous_pad()

    def set_previous_pad(self, pad: SourcePad | None) -> None:
        self._other.set_previous_pad(pad)

    def get_editor_type(self) -> str:
        return "StatelessSinkPad"

    def _get_queue(self) -> asyncio.Queue[Item | None]:
        return self._other._get_queue()
