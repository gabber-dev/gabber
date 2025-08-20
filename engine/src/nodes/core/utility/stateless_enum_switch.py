# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast
import logging

from core import pad
from core.node import Node, NodeMetadata


class StatelessEnumSwitch(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="utility", tags=["switch", "enum", "stateless"]
        )

    async def resolve_pads(self):
        selector = cast(pad.StatelessSinkPad, self.get_pad("selector"))
        if not selector:
            selector = pad.StatelessSinkPad(
                id="selector",
                owner_node=self,
                group="sink",
                type_constraints=[pad.types.Enum(options=[])],
            )
            self.pads.append(selector)

        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                owner_node=self,
                group="source",
                type_constraints=None,
            )
            self.pads.append(source)

        # Determine enum options from the previous pad connected to selector
        prev_pad = selector.get_previous_pad()
        enum_options: list[str] = []
        if prev_pad:
            prev_tcs = prev_pad.get_type_constraints()
            if prev_tcs and len(prev_tcs) == 1 and isinstance(prev_tcs[0], pad.types.Enum):
                enum_options = prev_tcs[0].options or []
            else:
                enum_options = []

        # Compute type constraints for value sinks and output from connections
        # Exclude the selector sink (enum) from data type intersection
        tcs: list[pad.types.BasePadType] | None = None
        for p in self.pads:
            if isinstance(p, pad.SinkPad) and p is not selector:
                prev = p.get_previous_pad()
                if prev:
                    tcs = pad.types.INTERSECTION(tcs, prev.get_type_constraints()) if tcs else prev.get_type_constraints()
            elif isinstance(p, pad.SourcePad):
                for np in p.get_next_pads():
                    tcs = pad.types.INTERSECTION(tcs, np.get_type_constraints()) if tcs else np.get_type_constraints()

        # Remove all existing value pads
        self.pads = [p for p in self.pads if not (isinstance(p, pad.StatelessSinkPad) and p.get_group() == "value")]
        
        # Create new pads for current enum options
        for option in enum_options:
            vp = pad.StatelessSinkPad(
                id=option,  # Use the original option as the ID
                owner_node=self,
                group="value",
                type_constraints=tcs,
            )
            self.pads.append(vp)

        # Reset references and set type constraints
        value_pads = [p for p in self.pads if isinstance(p, pad.StatelessSinkPad) and p.get_group() == "value"]
        selector.set_type_constraints([pad.types.Enum(options=enum_options)])
        for vp in value_pads:
            vp.set_type_constraints(tcs)
        source.set_type_constraints(tcs)

    def _get_value_lookup(self) -> dict[str, pad.StatelessSinkPad]:
        lookup: dict[str, pad.StatelessSinkPad] = {}
        for p in self.pads:
            if isinstance(p, pad.StatelessSinkPad) and p.get_group() == "value":
                lookup[p.get_id()] = p
        return lookup

    async def run(self):
        selector = cast(pad.StatelessSinkPad, self.get_pad_required("selector"))
        source = cast(pad.StatelessSourcePad, self.get_pad_required("source"))

        self._selected_value: str | None = None

        # Forward values from each input when it's the active selection
        async def forward_from_value_pad(vp: pad.StatelessSinkPad):
            async for v_item in vp:
                if self._selected_value == vp.get_id():
                    source.push_item(v_item.value, v_item.ctx)
                v_item.ctx.complete()

        tasks = [
            forward_from_value_pad(vp)
            for vp in self.pads
            if isinstance(vp, pad.StatelessSinkPad) and vp.get_group() == "value"
        ]

        # Consume selector to update active route
        async def consume_selector():
            async for s_item in selector:
                self._selected_value = s_item.value
                s_item.ctx.complete()

        tasks.append(consume_selector())

        if tasks:
            await asyncio.gather(*tasks)

