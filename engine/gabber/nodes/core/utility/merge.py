# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
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
                default_type_constraints=None,
                group="source",
            )

        num_sink_pads = cast(pad.PropertySinkPad | None, self.get_pad("num_sinks"))
        if not num_sink_pads:
            num_sink_pads = pad.PropertySinkPad(
                id="num_sinks",
                owner_node=self,
                default_type_constraints=[pad.types.Integer()],
                group="num_sinks",
                value=1,
            )

        sink_pads: list[pad.Pad] = []
        for i in range(num_sink_pads.get_value() or 1):
            pad_id = f"sink_{i}"
            sp = self.get_pad(pad_id)
            if not sp:
                sp = pad.StatelessSinkPad(
                    id=pad_id,
                    owner_node=self,
                    default_type_constraints=None,
                    group="sink",
                )
                sp.link_types_to_pad(source_pad)
            sink_pads.append(sp)

        for p in self.pads:
            if p.get_id().startswith("sink_") and p not in sink_pads:
                if isinstance(p, pad.StatelessSinkPad):
                    p.unlink_types_from_pad(source_pad)

        pads: list[pad.Pad] = [num_sink_pads, source_pad] + sink_pads
        self.pads = pads

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
