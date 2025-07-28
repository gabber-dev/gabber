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

    async def resolve_pads(self):
        source_pad = cast(pad.StatelessSourcePad | None, self.get_pad("source"))
        if not source_pad:
            self.pads.append(
                pad.StatelessSourcePad(
                    id="source",
                    owner_node=self,
                    type_constraints=None,
                    group="source",
                )
            )
            source_pad = cast(pad.StatelessSourcePad, self.get_pad("source"))

        sink_pads = cast(
            list[pad.SinkPad], [p for p in self.pads if p.get_group() == "sink"]
        )

        needs_new = True
        for p in sink_pads:
            if p.get_previous_pad() is None:
                needs_new = False
                break

        if needs_new:
            self.first_sink_pad = pad.StatelessSinkPad(
                id=f"sink_{len(sink_pads)}",
                owner_node=self,
                type_constraints=None,
                group="sink",
            )
            self.pads.append(self.first_sink_pad)

        sink_pads = cast(
            list[pad.SinkPad], [p for p in self.pads if p.get_group() == "sink"]
        )

        pads: list[pad.Pad] = [cast(pad.Pad, source_pad)] + sink_pads
        self.pads = pads
        tcs: list[pad.types.BasePadType] | None = None
        for p in self.pads:
            if isinstance(p, pad.SinkPad) and p.get_previous_pad():
                prev_pad = p.get_previous_pad()
                if prev_pad:
                    tcs = (
                        pad.types.INTERSECTION(tcs, prev_pad.get_type_constraints())
                        if tcs
                        else prev_pad.get_type_constraints()
                    )
            elif isinstance(p, pad.SourcePad):
                for np in p.get_next_pads():
                    tcs = (
                        pad.types.INTERSECTION(tcs, np.get_type_constraints())
                        if tcs
                        else np.get_type_constraints()
                    )
        for p in self.pads:
            p.set_type_constraints(tcs)

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
