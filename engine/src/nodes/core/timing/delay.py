# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast
import time

from core import node, pad
from core.node import NodeMetadata


class Delay(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Delays a stateless stream"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="timing", tags=["delay"])

    def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                group="sink",
                owner_node=self,
                default_type_constraints=None,
            )

        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                group="source",
                owner_node=self,
                default_type_constraints=None,
            )

        delay_ms = cast(pad.PropertySinkPad, self.get_pad("delay_ms"))
        if not delay_ms:
            delay_ms = pad.PropertySinkPad(
                id="delay_ms",
                group="delay_ms",
                owner_node=self,
                default_type_constraints=[pad.types.Integer(minimum=0)],
                value=1000,
            )

        sink.link_types_to_pad(source)

        self.pads = [sink, source, delay_ms]

    async def run(self):
        sink_pad = cast(pad.StatelessSinkPad, self.get_pad_required("sink"))
        source_pad = cast(pad.StatelessSourcePad, self.get_pad_required("source"))
        delay_pad = cast(pad.PropertySinkPad, self.get_pad_required("delay_ms"))
        delay_queue = asyncio.Queue[tuple[float, pad.RequestContext, Any] | None]()

        async def sink_task():
            async for item in sink_pad:
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
