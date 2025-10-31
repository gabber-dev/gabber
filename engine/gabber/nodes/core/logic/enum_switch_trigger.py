# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import cast

from gabber.core import pad
from gabber.core.node import Node, NodeMetadata
from gabber.core.types import pad_constraints


class EnumSwitchTrigger(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="utility", tags=["switch", "enum"]
        )

    def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                group="sink",
                owner_node=self,
                default_type_constraints=[pad_constraints.Enum(options=None)],
            )

        options: list[str] = []
        sink_tc = sink.get_type_constraints()
        if (
            sink_tc
            and isinstance(sink_tc[0], pad_constraints.Enum)
            and sink_tc[0].options
        ):
            options = sink_tc[0].options

        source_pads: list[pad.StatelessSourcePad] = []
        for o in options:
            s_p = cast(pad.StatelessSourcePad, self.get_pad(o))
            if not s_p:
                s_p = pad.StatelessSourcePad(
                    id=o,
                    owner_node=self,
                    group="value",
                    default_type_constraints=[pad_constraints.Trigger()],
                )
            source_pads.append(s_p)

        self.pads = [sink, *source_pads]

    async def run(self):
        sink = cast(pad.PropertySinkPad, self.get_pad_required("sink"))
        async for item in sink:
            source_pad = cast(pad.StatelessSourcePad, self.get_pad(item.value.value))
            if not source_pad:
                logging.error(
                    f"EnumSwitch received unknown value: {item.value}. Skipping item."
                )
                continue

            source_pad.push_item(item.value, item.ctx)
            item.ctx.complete()
