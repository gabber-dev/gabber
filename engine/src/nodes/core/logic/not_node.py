# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from core import node, pad
from core.node import NodeMetadata


class Not(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Inverts boolean values"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="logic", tags=["boolean", "invert"]
        )

    def initialize(self):
        self.sink = cast(pad.StatelessSinkPad, self.get_pad_required("sink"))
        self.source = cast(pad.StatelessSourcePad, self.get_pad_required("source"))

    async def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            self.pads.append(
                pad.StatelessSinkPad(
                    id="sink",
                    owner_node=self,
                    type_constraints=[pad.types.Boolean()],
                    group="sink",
                )
            )
            sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))

        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            self.pads.append(
                pad.StatelessSourcePad(
                    id="source",
                    owner_node=self,
                    type_constraints=[pad.types.Boolean()],
                    group="source",
                )
            )
            source = cast(pad.StatelessSourcePad, self.get_pad("source"))

        self.pads = [sink, source]

    async def run(self):
        async for item in self.sink:
            self.source.push_item(not item.value, item.ctx)
            item.ctx.complete()
