# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

from core import pad
from core.node import Node, NodeMetadata


class Merge(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Merges multiple data streams of similar type into one"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="utility", tags=["merge", "flow"])

    def resolve_pads(self):
        source_pad = cast(pad.StatelessSourcePad | None, self.get_pad("source"))
        if not source_pad:
            source_pad = pad.StatelessSourcePad(
                id="source",
                owner_node=self,
                type_constraints=[],
                group="source",
            )

        sink_pads = cast(
            list[pad.SinkPad], [p for p in self.pads if p.get_group() == "sink"]
        )

        needs_new = True
        for p in sink_pads:
            if p.get_previous_pad() is None:
                needs_new = False
                break

        if needs_new:
            sink_pads.append(
                pad.StatelessSinkPad(
                    id=f"sink_{len(sink_pads)}",
                    owner_node=self,
                    type_constraints=None,
                    group="sink",
                )
            )

        pads: list[pad.Pad] = [cast(pad.Pad, source_pad)] + sink_pads
        self.pads = pads
        sink_tcs: list[pad.types.BasePadType] | None = None
        for p in sink_pads:
            sink_tcs = pad.types.INTERSECTION(p.get_type_constraints(), sink_tcs)

        for p in sink_pads:
            p.set_type_constraints(sink_tcs)

        if sink_tcs is None:
            source_pad.set_type_constraints([])
        else:
            source_pad.set_type_constraints(sink_tcs)

    async def run(self):
        tasks = []
        source_pad = cast(pad.StatelessSourcePad, self.get_pad_required("source"))

        async def pad_task(p: pad.SinkPad):
            async for item in p:
                source_pad.push_item(item.value, item.ctx)
                item.ctx.complete()

        for p in self.pads:
            if isinstance(p, pad.SinkPad):
                tasks.append(pad_task(p))

        if len(tasks) > 0:
            await asyncio.gather(*tasks)
