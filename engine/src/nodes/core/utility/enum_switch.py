# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import cast

from core import pad
from core.node import Node, NodeMetadata


class PropertyEnumSwitch(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="utility", tags=["switch", "enum", "property"]
        )

    async def resolve_pads(self):
        sink = cast(pad.PropertySinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.PropertySinkPad(
                id="sink",
                group="sink",
                owner_node=self,
                type_constraints=[pad.types.Enum(options=[])],
                value="",
            )

        source = cast(pad.PropertySourcePad, self.get_pad("source"))
        if not source:
            source = pad.PropertySourcePad(
                id="source",
                group="source",
                owner_node=self,
                type_constraints=None,
                value="",
            )

        prev_pad = sink.get_previous_pad()
        if not prev_pad:
            sink.set_value(None)
            source.set_value(None)
            sink.set_type_constraints([pad.types.Enum(options=[])])
            source.set_type_constraints(None)
            self.pads = [sink, source]
            return

        prev_tcs = prev_pad.get_type_constraints()
        if not prev_tcs or len(prev_tcs) != 1:
            raise ValueError("Previous pad must have exactly one type constraint.")

        prev_tc = prev_tcs[0]
        if not isinstance(prev_tc, pad.types.Enum):
            raise ValueError("Previous pad type constraint must be an Enum.")

        sink.set_type_constraints([pad.types.Enum(options=prev_tc.options)])
        tcs = None
        for v_pad in self.get_value_lookup().values():
            prev_v_pad = v_pad.get_previous_pad()
            if prev_v_pad:
                tcs = pad.types.INTERSECTION(tcs, prev_v_pad.get_type_constraints())
            v_pad.set_type_constraints(tcs)

        source.set_type_constraints(tcs)

        options = prev_tc.options
        if options is None:
            options = []

        value_pads = [
            p
            for p in self.pads
            if isinstance(p, pad.PropertySinkPad) and p.get_group() == "value"
        ]
        existing_options = {p.get_id() for p in value_pads}
        for option in options:
            if option not in existing_options:
                value_pads.append(
                    pad.PropertySinkPad(
                        id=option,
                        group="value",
                        owner_node=self,
                        type_constraints=tcs,
                        value=None,
                    )
                )

        selected_value = sink.get_value()
        if selected_value in self.get_value_lookup():
            source.set_value(self.get_value_lookup()[selected_value].get_value())

        self.pads = [sink, source] + value_pads

    def get_value_lookup(self) -> dict[str, pad.PropertySinkPad]:
        value_lookup: dict[str, pad.PropertySinkPad] = {}
        for p in self.pads:
            if isinstance(p, pad.PropertySinkPad) and p.get_group() == "value":
                value_lookup[p.get_id()] = p
        return value_lookup

    async def run(self):
        sink = cast(pad.PropertySinkPad, self.get_pad_required("sink"))
        source = cast(pad.PropertySourcePad, self.get_pad_required("source"))
        value_lookup = self.get_value_lookup()
        async for item in sink:
            print("PropertyEnumSwitch received item", item.value, item.ctx)
            value_pad = value_lookup.get(item.value)
            if not value_pad:
                logging.warning(
                    f"PropertyEnumSwitch received unknown value: {item.value}. Skipping item."
                )
                continue
            source.push_item(value_pad.get_value(), item.ctx)
            item.ctx.complete()

