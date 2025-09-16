# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from gabber.core import pad
from gabber.core.node import Node, NodeMetadata


class Gate(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="logic", tags=["gate"])

    def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                group="sink",
                owner_node=self,
                default_type_constraints=None,
            )

        open_pad = cast(pad.PropertySinkPad, self.get_pad("open"))
        if not open_pad:
            open_pad = pad.PropertySinkPad(
                id="open",
                group="open",
                owner_node=self,
                default_type_constraints=[pad.types.Boolean()],
            )

        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                group="source",
                owner_node=self,
                default_type_constraints=None,
            )

        sink.link_types_to_pad(source)
        self.pads = [sink, open_pad, source]

    async def run(self):
        sink = cast(pad.PropertySinkPad, self.get_pad_required("sink"))
        open_pad = cast(pad.PropertySinkPad, self.get_pad_required("open"))
        source = cast(pad.StatelessSourcePad, self.get_pad_required("source"))
        async for item in sink:
            if open_pad.get_value():
                source.push_item(item.value, item.ctx)

            item.ctx.complete()
