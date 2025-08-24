# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from core import node, pad
from core.node import NodeMetadata


class String(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Stores and manages string values"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="primitive", tags=["storage", "string"]
        )

    async def resolve_pads(self):
        set_pad = cast(pad.StatelessSinkPad | None, self.get_pad("set"))
        if not set_pad:
            set_pad = pad.StatelessSinkPad(
                id="set",
                owner_node=self,
                group="set",
                type_constraints=[pad.types.String()],
            )

        emit = cast(pad.StatelessSinkPad | None, self.get_pad("emit"))
        if not emit:
            emit = pad.StatelessSinkPad(
                id="emit",
                owner_node=self,
                group="emit",
                type_constraints=[pad.types.Trigger()],
            )

        value = cast(pad.PropertySourcePad | None, self.get_pad("value"))
        if not value:
            value = pad.PropertySourcePad(
                id="value",
                group="value",
                owner_node=self,
                type_constraints=[pad.types.String()],
                value="",
            )

        changed = cast(pad.StatelessSourcePad | None, self.get_pad("changed"))
        if not changed:
            changed = pad.StatelessSourcePad(
                id="changed",
                group="changed",
                owner_node=self,
                type_constraints=[pad.types.String()],
            )

        self.pads = [set_pad, emit, value, changed]

    async def run(self):
        emit = cast(pad.StatelessSinkPad, self.get_pad_required("emit"))
        set_pad = cast(pad.StatelessSinkPad, self.get_pad_required("set"))
        value = cast(pad.PropertySourcePad, self.get_pad_required("value"))
        changed_pad = cast(pad.StatelessSourcePad, self.get_pad_required("changed"))

        async def emit_task():
            async for item in emit:
                value.push_item(value.get_value(), item.ctx)
                item.ctx.complete()

        async def set_task():
            async for item in set_pad:
                changed = False
                if value.get_value() != item.value:
                    changed = True
                value.push_item(item.value, item.ctx)
                if changed:
                    changed_pad.push_item(item.value, item.ctx)
                item.ctx.complete()

        await asyncio.gather(
            emit_task(),
            set_task(),
        )
