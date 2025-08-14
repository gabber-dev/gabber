# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast
import time

from core import node, pad
from core.node import NodeMetadata


class StartRequest(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Starts a request"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="synchronization", tags=["request"]
        )

    async def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                group="sink",
                owner_node=self,
                type_constraints=None,
            )
            self.pads.append(sink)

        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                group="source",
                owner_node=self,
                type_constraints=None,
            )
            self.pads.append(source)

        next_pads = source.get_next_pads()
        tcs: list[pad.types.BasePadType] | None = None
        for next_pad in next_pads:
            tcs = pad.types.INTERSECTION(tcs, next_pad.get_type_constraints())

        prev_pad = sink.get_previous_pad()
        if prev_pad:
            tcs = pad.types.INTERSECTION(tcs, prev_pad.get_type_constraints())

        sink.set_type_constraints(tcs)
        source.set_type_constraints(tcs)

    async def run(self):
        sink_pad = cast(pad.StatelessSinkPad, self.get_pad_required("sink"))
        source_pad = cast(pad.StatelessSourcePad, self.get_pad_required("source"))
        delay_pad = cast(pad.PropertySinkPad, self.get_pad_required("delay_ms"))
        delay_queue = asyncio.Queue[tuple[float, pad.RequestContext, Any] | None]()

        async def sink_task():
            async for item in sink_pad:
                logging.info("NEIL got item %s", item)
                delay = cast(int, delay_pad.get_value())
                current_time = time.time()
                delay_queue.put_nowait(
                    (current_time + delay / 1000.0, item.ctx, item.value)
                )
            delay_queue.put_nowait(None)

        async def source_task():
            while True:
                item = await delay_queue.get()
                if item is None:
                    break

                delay_time, ctx, value = item
                delta = delay_time - time.time()
                if delta > 0:
                    await asyncio.sleep(delta)
                source_pad.push_item(value, ctx)
                ctx.complete()

        await asyncio.gather(sink_task(), source_task())
