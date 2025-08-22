# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import cast

from core import pad
from core.node import Node, NodeMetadata


class EnumSwitchTrigger(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="utility", tags=["switch", "enum"]
        )

    async def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                group="sink",
                owner_node=self,
                type_constraints=[pad.types.Enum(options=[])],
            )

        prev_pad = sink.get_previous_pad()
        options: list[str] = []
        if prev_pad:
            prev_tc = prev_pad.get_type_constraints()
            if prev_tc and len(prev_tc) == 1 and isinstance(prev_tc[0], pad.types.Enum):
                sink.set_type_constraints([pad.types.Enum(options=prev_tc[0].options)])
                options = prev_tc[0].options if prev_tc[0].options else []

        source_pads: list[pad.StatelessSourcePad] = []
        for o in options:
            s_p = cast(pad.StatelessSourcePad, self.get_pad(o))
            if not s_p:
                s_p = pad.StatelessSourcePad(
                    id=o,
                    owner_node=self,
                    group="value",
                    type_constraints=[pad.types.Trigger()],
                )
            source_pads.append(s_p)

        self.pads = [sink, *source_pads]

    async def run(self):
        sink = cast(pad.PropertySinkPad, self.get_pad_required("sink"))
        async for item in sink:
            source_pad = cast(pad.StatelessSourcePad, self.get_pad(item.value))
            if not source_pad:
                logging.error(
                    f"EnumSwitch received unknown value: {item.value}. Skipping item."
                )
                continue

            source_pad.push_item(item.value, item.ctx)
            item.ctx.complete()
