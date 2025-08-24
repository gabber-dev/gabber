# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import TYPE_CHECKING, Literal

from core.pad.pad import SourcePad

from . import types
from .pad import SinkPad

if TYPE_CHECKING:
    from core.node import Node


class StatelessSourcePad(SourcePad):
    def __init__(
        self,
        *,
        id: str,
        group: str,
        owner_node: "Node",
        type_constraints: list[types.BasePadType] | None = None,
    ):
        self._id = id
        self._group = group
        self._owner_node = owner_node
        self._type_constraints = type_constraints
        self._next_pads: list[SinkPad] = []

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

    def set_type_constraints(self, constraints: list[types.BasePadType] | None) -> None:
        self._type_constraints = constraints

    def get_editor_type(self) -> str:
        return "StatelessSourcePad"

    def get_direction(self) -> Literal["source"] | Literal["sink"]:
        return "source"

    def get_next_pads(self) -> list[SinkPad]:
        return self._next_pads[:]

    def set_next_pads(self, pads: list[SinkPad]) -> None:
        self._next_pads = pads
