# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import cast

from gabber.core import pad
from gabber.core.node import Node, NodeMetadata
from gabber.core.types import pad_constraints

ALLOWED_VALUE_TYPES = [
    pad_constraints.String(),
    pad_constraints.Integer(),
    pad_constraints.Boolean(),
    pad_constraints.Float(),
    pad_constraints.ContextMessage(),
]


class EnumSwitchProperty(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="utility", tags=["switch", "enum"]
        )

    def resolve_pads(self):
        sink = cast(pad.PropertySinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.PropertySinkPad(
                id="sink",
                group="sink",
                owner_node=self,
                default_type_constraints=[pad_constraints.Enum(options=None)],
                value=None,
            )

        options: list[str] = []
        sink_tc = sink.get_type_constraints()
        if (
            sink_tc
            and isinstance(sink_tc[0], pad_constraints.Enum)
            and sink_tc[0].options
        ):
            options = sink_tc[0].options

        value_pads: list[pad.PropertySinkPad] = []
        for o in options:
            s_p = cast(pad.PropertySinkPad, self.get_pad(o))
            if not s_p:
                s_p = pad.PropertySinkPad(
                    id=o,
                    owner_node=self,
                    group="value",
                    default_type_constraints=ALLOWED_VALUE_TYPES,
                    value=None,
                )
            value_pads.append(s_p)

        source_pad = cast(pad.PropertySourcePad, self.get_pad("source"))
        if not source_pad:
            source_pad = pad.PropertySourcePad(
                id="source",
                owner_node=self,
                group="source",
                default_type_constraints=ALLOWED_VALUE_TYPES,
                value=None,
            )

        if len(value_pads) > 0:
            for vp in value_pads[1:]:
                vp.link_types_to_pad(value_pads[0])

            source_pad.link_types_to_pad(value_pads[0])
        else:
            source_pad.unlink_all()

        v = self.get_source_value(sink, value_pads)
        source_pad._set_value(v)
        self.pads = [sink, *value_pads, source_pad]

    def get_source_value(
        self, sink_pad: pad.PropertySinkPad, value_pads: list[pad.PropertySinkPad]
    ):
        vp = next(
            (p for p in value_pads if p.get_id() == sink_pad.get_value().value), None
        )
        if not vp:
            return None
        else:
            return vp.get_value()

    async def run(self):
        sink = cast(pad.PropertySinkPad, self.get_pad_required("sink"))
        value_pads = cast(
            list[pad.PropertySinkPad],
            [p for p in self.pads if p.get_group() == "value"],
        )
        source_pad = cast(pad.PropertySourcePad, self.get_pad_required("source"))
        async for item in sink:
            v = self.get_source_value(sink, value_pads)
            if v is None:
                logging.error(
                    f"EnumSwitchProperty received unknown value: {item.value}. Skipping item."
                )
                item.ctx.complete()
                continue

            source_pad.push_item(v, item.ctx)
            item.ctx.complete()
