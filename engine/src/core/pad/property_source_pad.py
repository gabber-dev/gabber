# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import TYPE_CHECKING, Any, Literal


from .pad import PropertyPad, SinkPad, SourcePad, NOTIFIABLE_TYPES
from .types import BasePadType

if TYPE_CHECKING:
    from core.node import Node


class PropertySourcePad(SourcePad, PropertyPad):
    def __init__(
        self,
        *,
        id: str,
        group: str,
        owner_node: "Node",
        type_constraints: list[BasePadType] | None,
        value: Any,
    ):
        self._id = id
        self._group = group
        self._owner_node = owner_node
        self._type_constraints = type_constraints
        self._value = value
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

    def set_type_constraints(self, constraints: list[BasePadType] | None) -> None:
        self._type_constraints = constraints

    def get_previous_pad(self) -> SourcePad | None:
        return self.previous_pad

    def set_previous_pad(self, pad: SourcePad | None) -> None:
        self.previous_pad = pad

    def get_editor_type(self) -> str:
        return "PropertySourcePad"

    def get_direction(self) -> Literal["source"] | Literal["sink"]:
        return "source"

    def get_value(self) -> Any:
        return self._value

    def set_value(self, value: Any):
        self._value = value
        if isinstance(value, NOTIFIABLE_TYPES):
            self._notify_update(value)
        for np in self.get_next_pads():
            if isinstance(np, PropertyPad):
                np.set_value(value)

    def get_next_pads(self) -> list[SinkPad]:
        return self._next_pads[:]

    def set_next_pads(self, pads: list[SinkPad]) -> None:
        self._next_pads = pads
