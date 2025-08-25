# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import Any, cast

from core import pad
from core.node import Node, NodeMetadata


class TypeConstraint(Node):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="utility", tags=[])

    def resolve_pads(self):
        type_selector = cast(pad.PropertySinkPad, self.get_pad("type_selector"))
        if not type_selector:
            type_selector = pad.PropertySinkPad(
                id="type_selector",
                group="type_selector",
                owner_node=self,
                default_type_constraints=[
                    pad.types.Enum(
                        options=["string", "integer", "float", "boolean", "trigger"]
                    )
                ],
            )

        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                owner_node=self,
                group="sink",
                default_type_constraints=None,
            )

        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                owner_node=self,
                group="source",
                default_type_constraints=None,
            )

        selected_type = type_selector.get_value()
        default_value: Any | None = None
        if selected_type == "string":
            sink.set_default_type_constraints([pad.types.String()])
            source.set_default_type_constraints([pad.types.String()])
            default_value = ""
        elif selected_type == "integer":
            sink.set_default_type_constraints([pad.types.Integer()])
            source.set_default_type_constraints([pad.types.Integer()])
            default_value = 0
        elif selected_type == "float":
            sink.set_default_type_constraints([pad.types.Float()])
            source.set_default_type_constraints([pad.types.Float()])
            default_value = 0.0
        elif selected_type == "boolean":
            sink.set_default_type_constraints([pad.types.Boolean()])
            source.set_default_type_constraints([pad.types.Boolean()])
            default_value = False
        elif selected_type == "trigger":
            sink.set_default_type_constraints([pad.types.Trigger()])
            source.set_default_type_constraints([pad.types.Trigger()])
            default_value = None
        
        self.pads = [sink, source, type_selector]

        prev_pad = sink.get_previous_pad()
        next_pads = source.get_next_pads()
        if prev_pad:
            prev_tcs = prev_pad.get_type_constraints()
            sink_tcs = sink.get_type_constraints()
            intersection = pad.types.INTERSECTION(prev_tcs, sink_tcs)
            if intersection is not None and len(intersection) == 0:
                sink.disconnect()

            old_sink = sink
            if isinstance(prev_pad, pad.PropertyPad):
                prev_value = prev_pad.get_value()
                value = prev_value if prev_value is not None else default_value
                sink = pad.PropertySinkPad(
                    owner_node=self,
                    id=sink.get_id(),
                    group=sink.get_group(),
                    default_type_constraints=intersection,
                    value=value,
                )
                prev_pad.disconnect(old_sink)
                prev_pad.connect(sink)
                source = pad.PropertySourcePad(
                    owner_node=self,
                    id=source.get_id(),
                    group=source.get_group(),
                    default_type_constraints=intersection,
                    value=value,
                )
                if not prev_value:
                    prev_pad.set_value(value)
                for np in next_pads:
                    np.disconnect()
                    source.connect(np)
            else:
                sink = pad.StatelessSinkPad(
                    owner_node=self,
                    id=sink.get_id(),
                    group=sink.get_group(),
                    default_type_constraints=intersection,
                )
                prev_pad.disconnect(old_sink)
                prev_pad.connect(sink)
                source = pad.StatelessSourcePad(
                    owner_node=self,
                    id=source.get_id(),
                    group=source.get_group(),
                    default_type_constraints=intersection,
                )
                for np in next_pads:
                    np.disconnect()
                    source.connect(np)

        for np in next_pads:
            np_tcs = np.get_type_constraints()
            source_tcs = source.get_type_constraints()
            intersection = pad.types.INTERSECTION(np_tcs, source_tcs)
            if intersection is not None and len(intersection) == 0:
                source.disconnect(np)

        self.pads = [sink, source, type_selector]

    async def run(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad_required("sink"))
        source = cast(pad.StatelessSourcePad, self.get_pad_required("source"))
        async for item in sink:
            source.push_item(item.value, item.ctx)
            item.ctx.complete()
