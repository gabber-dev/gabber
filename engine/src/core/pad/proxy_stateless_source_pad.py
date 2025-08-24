# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import TYPE_CHECKING

from core.pad import Pad, ProxyPad, SinkPad, SourcePad, types

if TYPE_CHECKING:
    from core.node import Node


class ProxyStatelessSourcePad(SourcePad, ProxyPad):
    def __init__(self, *, id: str, group: str, owner_node: "Node", other: SourcePad):
        self._id = id
        self._group = group
        self._owner_node = owner_node
        self._other = other
        self._my_next_pads: list[SinkPad] = []

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

    def get_editor_type(self) -> str:
        return "StatelessSourcePad"

    def get_next_pads(self) -> list[SinkPad]:
        return self._my_next_pads[:]

    def set_next_pads(self, pads: list[SinkPad]) -> None:
        self._my_next_pads = pads
        full_other_next_pads = self._other.get_next_pads()
        other_next_pads = [p for p in full_other_next_pads if p not in pads]
        self._other.set_next_pads(other_next_pads + pads)
