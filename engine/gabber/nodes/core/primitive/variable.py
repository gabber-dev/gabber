# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast, Any

from gabber.core import node, pad
from gabber.core.node import NodeMetadata
from gabber.core.types import pad_constraints


ALLOWED_TYPES = [
    pad_constraints.String(),
    pad_constraints.Integer(),
    pad_constraints.Boolean(),
    pad_constraints.Float(),
]


class Variable(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Stores and manages string values"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="primitive", tags=["storage", "string"]
        )

    def resolve_pads(self):
        set_pad = cast(pad.StatelessSinkPad | None, self.get_pad("set"))
        if not set_pad:
            set_pad = pad.StatelessSinkPad(
                id="set",
                owner_node=self,
                group="set",
                default_type_constraints=ALLOWED_TYPES,
            )

        emit = cast(pad.StatelessSinkPad | None, self.get_pad("emit"))
        if not emit:
            emit = pad.StatelessSinkPad(
                id="emit",
                owner_node=self,
                group="emit",
                default_type_constraints=[pad_constraints.Trigger()],
            )

        emit_source = cast(pad.StatelessSourcePad | None, self.get_pad("emit_source"))
        if not emit_source:
            emit_source = pad.StatelessSourcePad(
                id="emit_source",
                group="emit_source",
                owner_node=self,
                default_type_constraints=ALLOWED_TYPES,
            )

        current_value = cast(
            pad.PropertySourcePad[Any] | None, self.get_pad("current_value")
        )
        if not current_value:
            current_value = pad.PropertySourcePad[Any](
                id="current_value",
                group="current_value",
                owner_node=self,
                default_type_constraints=ALLOWED_TYPES,
                value=None,
            )

        emit_source.link_types_to_pad(set_pad)
        current_value.link_types_to_pad(set_pad)

        tc = set_pad.get_type_constraints()
        if tc is None or len(tc) != 1:
            current_value._set_value(None)
        else:
            cv = current_value.get_value()
            if isinstance(tc[0], pad_constraints.String) and not isinstance(cv, str):
                current_value._set_value("")
            elif isinstance(tc[0], pad_constraints.Integer) and not isinstance(cv, int):
                current_value._set_value(0)
            elif isinstance(tc[0], pad_constraints.Boolean) and not isinstance(
                cv, bool
            ):
                current_value._set_value(False)
            elif isinstance(tc[0], pad_constraints.Float) and not isinstance(cv, float):
                current_value._set_value(0.0)

        self.pads = [set_pad, emit, current_value, emit_source]

    async def run(self):
        emit = cast(pad.StatelessSinkPad, self.get_pad_required("emit"))
        emit_source = cast(pad.StatelessSourcePad, self.get_pad_required("emit_source"))
        set_pad = cast(pad.StatelessSinkPad, self.get_pad_required("set"))
        value = cast(pad.PropertySourcePad, self.get_pad_required("current_value"))

        async def emit_task():
            async for item in emit:
                emit_source.push_item(value.get_value(), item.ctx)
                item.ctx.complete()

        async def set_task():
            async for item in set_pad:
                value.push_item(item.value, item.ctx)
                item.ctx.complete()

        await asyncio.gather(
            emit_task(),
            set_task(),
        )
