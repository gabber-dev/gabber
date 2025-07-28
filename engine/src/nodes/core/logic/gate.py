# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from core import node, pad
from core.node import NodeMetadata


class Gate(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Controls data flow based on a boolean condition"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="logic", tags=["control", "gate"])

    def initialize(self):
        self.sink = cast(pad.StatelessSinkPad, self.get_pad_required("sink"))
        self.source = cast(pad.StatelessSourcePad, self.get_pad_required("source"))
        self.open = cast(pad.PropertySinkPad, self.get_pad_required("open"))

    async def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            self.pads.append(
                pad.StatelessSinkPad(
                    id="sink",
                    owner_node=self,
                    type_constraints=None,
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
                    type_constraints=None,
                    group="source",
                )
            )
            source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        open_pad = cast(pad.PropertySinkPad, self.get_pad("open"))
        if not open_pad:
            self.pads.append(
                pad.PropertySinkPad(
                    id="open",
                    owner_node=self,
                    type_constraints=[pad.types.Boolean()],
                    group="open",
                    value=True,
                )
            )
            open_pad = cast(pad.PropertySinkPad, self.get_pad("open"))
        tcs: list[pad.types.BasePadType] | None = None
        prev_pad = sink.get_previous_pad()
        if prev_pad:
            tcs = pad.types.INTERSECTION(
                prev_pad.get_type_constraints(),
                source.get_type_constraints(),
            )
        for np in source.get_next_pads():
            np_tcs = np.get_type_constraints()
            tcs = (
                pad.types.INTERSECTION(tcs, np_tcs)
                if tcs
                else np.get_type_constraints()
            )

        sink.set_type_constraints(tcs)
        source.set_type_constraints(tcs)
        self.pads = [sink, open_pad, source]

    async def run(self):
        async for item in self.sink:
            if self.open.get_value():
                self.source.push_item(item.value, item.ctx)
            item.ctx.complete()
