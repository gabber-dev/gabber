# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast
import time

from gabber.core import node, pad
from gabber.core.node import NodeMetadata
from gabber.core.types import pad_constraints


class Ticker(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Increments a counter at a specified interval"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="timing", tags=["ticker"])

    def resolve_pads(self):
        tick = cast(pad.PropertySourcePad, self.get_pad("tick"))
        if not tick:
            tick = pad.PropertySourcePad(
                id="tick",
                group="tick",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer(minimum=0)],
                value=0,
            )

        interval_ms = cast(pad.PropertySinkPad, self.get_pad("interval_ms"))
        if not interval_ms:
            interval_ms = pad.PropertySinkPad(
                id="interval_ms",
                group="interval_ms",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer(minimum=0)],
                value=1000,
            )

        reset = cast(pad.StatelessSinkPad, self.get_pad("reset"))
        if not reset:
            reset = pad.StatelessSinkPad(
                id="reset",
                group="reset",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        active = cast(pad.PropertySinkPad, self.get_pad("active"))
        if not active:
            active = pad.PropertySinkPad(
                id="active",
                group="active",
                owner_node=self,
                default_type_constraints=[pad_constraints.Boolean()],
                value=True,
            )

        self.pads = [tick, interval_ms, active, reset]

    async def run(self):
        tick_pad = cast(pad.PropertySourcePad, self.get_pad_required("tick"))
        interval_pad = cast(pad.PropertySinkPad, self.get_pad_required("interval_ms"))
        reset_pad = cast(pad.StatelessSinkPad, self.get_pad_required("reset"))
        active_pad = cast(pad.PropertySinkPad, self.get_pad_required("active"))
        active_hold = asyncio.Event()
        if active_pad.get_value():
            active_hold.set()

        last_time = time.time()

        async def reset_task():
            nonlocal last_time
            async for item in reset_pad:
                tick_pad.set_value(0)
                last_time = time.time()
                item.ctx.complete()

        async def tick_task():
            nonlocal last_time
            while True:
                await active_hold.wait()
                interval_ms = interval_pad.get_value()
                if not isinstance(interval_ms, int) or interval_ms <= 0:
                    logging.warning(
                        "Interval must be a positive integer. Using default of 1000 ms."
                    )
                    # Sleep to prevent busy loop
                    await asyncio.sleep(1)
                    continue

                current_time = time.time()
                delta = current_time - last_time
                if delta >= interval_ms / 1000.0:
                    current_tick = tick_pad.get_value()
                    if not isinstance(current_tick, int):
                        current_tick = 0
                    new_tick = current_tick + 1
                    if not active_hold.is_set():
                        continue
                    tick_pad.push_item(
                        new_tick,
                        pad.RequestContext(
                            parent=None, originator=self.id, publisher_metadata=None
                        ),
                    )
                    last_time = current_time + delta - (interval_ms / 1000.0)
                else:
                    sleep_time = (interval_ms / 1000.0) - delta
                    await asyncio.sleep(sleep_time)

        async def active_task():
            nonlocal last_time
            async for item in active_pad:
                if item.value is False:
                    await asyncio.sleep(0.1)
                    active_hold.clear()
                    last_time = time.time()
                else:
                    active_hold.set()
                item.ctx.complete()

        await asyncio.gather(reset_task(), active_task(), tick_task())
