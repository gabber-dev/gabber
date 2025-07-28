# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from core import pad
from core.node import Node, NodeMetadata


class Noop(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Pass through data without modification"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="utility", tags=[])

    async def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                owner_node=self,
                group="sink",
                type_constraints=None,
            )
            self.pads.append(sink)

        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                owner_node=self,
                group="source",
                type_constraints=None,
            )
            self.pads.append(source)
        tcs: list[pad.types.BasePadType] | None = None
        prev_pad = sink.get_previous_pad()
        if prev_pad:
            sink.set_type_constraints(prev_pad.get_type_constraints())
            tcs = pad.types.INTERSECTION(tcs, prev_pad.get_type_constraints())

        if source.get_next_pads():
            for np in source.get_next_pads():
                np_tcs = np.get_type_constraints()
                tcs = pad.types.INTERSECTION(tcs, np_tcs)

        sink.set_type_constraints(tcs)
        source.set_type_constraints(tcs)

    async def run(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad_required("sink"))
        source = cast(pad.StatelessSourcePad, self.get_pad_required("source"))
        async for item in sink:
            source.push_item(item.value, item.ctx)
            item.ctx.complete()
