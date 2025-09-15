# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from core import node, pad
from typing import cast


class And(node.Node):
    @classmethod
    def get_metadata(cls) -> node.NodeMetadata:
        return node.NodeMetadata(primary="core", secondary="logic", tags=["and"])

    def resolve_pads(self):
        num_inputs_pad = cast(pad.PropertySinkPad, self.get_pad("num_inputs"))
        if not num_inputs_pad:
            num_inputs_pad = pad.PropertySinkPad(
                id="num_inputs",
                group="num_inputs",
                owner_node=self,
                default_type_constraints=[pad.types.Integer()],
                value=2,
            )

        num_inputs = num_inputs_pad.get_value()
        if num_inputs is None or num_inputs < 2:
            num_inputs = 2
            num_inputs_pad.set_value(2)

        input_pads: list[pad.PropertySinkPad] = []
        for i in range(num_inputs):
            input_pad = cast(pad.PropertySinkPad, self.get_pad(f"input_{i + 1}"))
            if not input_pad:
                input_pad = pad.PropertySinkPad(
                    id=f"input_{i + 1}",
                    group="input",
                    owner_node=self,
                    default_type_constraints=[pad.types.Boolean()],
                    value=False,
                )
            input_pads.append(input_pad)

        for p in self.pads:
            if p.get_group() != "num_inputs":
                continue
            if not isinstance(p, pad.PropertySinkPad):
                self.pads.remove(p)
                continue
            if p not in input_pads:
                input_pads.remove(p)

        source = cast(pad.PropertySourcePad, self.get_pad("source"))
        if not source:
            source = pad.PropertySourcePad(
                id="source",
                group="source",
                owner_node=self,
                default_type_constraints=[pad.types.Boolean()],
                value=False,
            )

        self.pads = cast(list[pad.Pad], [num_inputs_pad] + input_pads + [source])
        source.set_value(self.check_result())

    def check_result(self) -> bool:
        input_pads = [
            p
            for p in self.pads
            if p.get_group() == "input" and isinstance(p, pad.PropertySinkPad)
        ]
        for p in input_pads:
            if not p.get_value():
                return False
        return True

    async def run(self):
        input_pads = [
            p
            for p in self.pads
            if p.get_group() == "input" and isinstance(p, pad.PropertySinkPad)
        ]
        source = cast(pad.PropertySourcePad, self.get_pad_required("source"))

        async def pad_task(p: pad.PropertySinkPad):
            async for item in p:
                p.set_value(bool(item.value))
                source.set_value(self.check_result())
                item.ctx.complete()

        await asyncio.gather(*(pad_task(p) for p in input_pads))
