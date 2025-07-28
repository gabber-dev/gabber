# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

from core import pad
from core.node import Node, NodeMetadata


class WaitForRequest(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Waits for a specific trigger before proceeding"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="utility", tags=["control", "wait"]
        )

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
        for p in self.pads:
            if isinstance(p, pad.SinkPad):
                prev_pad = p.get_previous_pad()
                if not prev_pad:
                    continue
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
        sink = cast(pad.StatelessSinkPad, self.get_pad_required("sink"))
        source = cast(pad.StatelessSourcePad, self.get_pad_required("source"))
        async for item in sink:
            done_fut = asyncio.Future()
            item.ctx.add_done_callback(done_fut.set_result)
            item.ctx.complete()
            await done_fut
            source.push_item(
                item.value, pad.RequestContext(parent=None, originator=self.id)
            )
