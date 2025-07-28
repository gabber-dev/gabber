# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import Any, cast

from core import pad
from core.node import Node, NodeMetadata


class UnpackObject(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="utility", tags=["trigger", "start"]
        )

    async def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                group="sink",
                owner_node=self,
                type_constraints=[pad.types.Object()],
            )
        input_tcs = sink.get_type_constraints()
        if not input_tcs or len(input_tcs) != 1:
            raise ValueError("Input pad must have exactly one type constraint.")

        prev_pad = sink.get_previous_pad()
        if not prev_pad:
            self.pads = [sink]
            return

        prev_tcs = prev_pad.get_type_constraints()
        if not prev_tcs or len(prev_tcs) != 1:
            raise ValueError("Previous pad must have exactly one type constraint.")

        prev_tc = prev_tcs[0]
        if not isinstance(prev_tc, pad.types.Object):
            raise ValueError("Previous pad type constraint must be an Object.")

        prev_schema = prev_tc.object_schema
        if not prev_schema:
            raise ValueError("Previous pad Object type must have a schema.")

        sink.set_type_constraints([pad.types.Object(object_schema=prev_schema)])
        self.resolve_output_pads(prev_schema)

    def resolve_output_pads(self, schema: dict[str, Any]):
        pad_types = pad.types.json_schema_to_types(schema)
        output_pads = [p for p in self.pads if p.get_group() == "output"]
        key_set = set(pad_types.keys())
        for key, pad_type in pad_types.items():
            output_pad = next((p for p in output_pads if p.get_id() == key), None)
            if output_pad:
                output_pad.set_type_constraints([pad_type])
            else:
                output_pad = pad.StatelessSourcePad(
                    id=f"{key}",
                    group="output",
                    owner_node=self,
                    type_constraints=[pad_type],
                )
                self.pads.append(output_pad)

        # Remove any output pads that are no longer in the schema
        for output_pad in output_pads:
            if output_pad.get_id() not in key_set:
                self.pads.remove(output_pad)

    async def run(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad_required("sink"))
        async for item in sink:
            if not isinstance(item.value, dict):
                logging.error("UnpackObject received an item that is not a dictionary.")
                continue

            keys = item.value.keys()
            output_pads = [p for p in self.pads if p.get_group() == "output"]
            for k in keys:
                output_pad = next(
                    (p for p in output_pads if p.get_id() == f"{k}"), None
                )
                if not output_pad:
                    logging.error(f"No output pad found for key '{k}'.")
                    continue
                value = item.value.get(k)
                # TODO: handle required keys
                if value is None:
                    continue

                cast(pad.SourcePad, output_pad).push_item(value, item.ctx)
            item.ctx.complete()
