# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import TYPE_CHECKING, Generic, TypeVar

from ..pad.pad import Item, SourcePad

from .pad import SinkPad
from ..types import pad_constraints, runtime

if TYPE_CHECKING:
    from ..node import Node

T = TypeVar("T", bound=runtime.RuntimePadValue)


class StatelessSinkPad(SinkPad[T], Generic[T]):
    def __init__(
        self,
        *,
        id: str,
        group: str,
        owner_node: "Node",
        default_type_constraints: list[pad_constraints.BasePadType] | None = None,
    ):
        super().__init__()
        self._id = id
        self._group = group
        self._owner_node = owner_node
        self._type_constraints = default_type_constraints
        self._default_type_constraints = default_type_constraints
        self._previous_pad: SourcePad[T] | None = None
        self._queue = asyncio.Queue[Item[T] | None]()

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

    def get_default_type_constraints(self):
        return self._default_type_constraints

    def set_default_type_constraints(
        self, constraints: list[pad_constraints.BasePadType] | None
    ) -> None:
        self._default_type_constraints = constraints
        self._resolve_type_constraints()

    def set_type_constraints(
        self, constraints: list[pad_constraints.BasePadType] | None
    ) -> None:
        self._type_constraints = constraints

    def get_previous_pad(self) -> SourcePad[T] | None:
        return self._previous_pad

    def set_previous_pad(self, pad: SourcePad[T] | None) -> None:
        self._previous_pad = pad

    def get_editor_type(self) -> str:
        return "StatelessSinkPad"

    def _get_queue(self) -> asyncio.Queue[Item[T] | None]:
        return self._queue
