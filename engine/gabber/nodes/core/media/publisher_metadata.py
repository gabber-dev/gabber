# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from gabber.core import node, pad
from gabber.core.node import NodeMetadata
from gabber.core.types import pad_constraints


class PublisherMetadata(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Extract metadata values from the publisher metadata dictionary."

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="media", tags=["metadata"])

    def resolve_pads(self):
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

        key_sink = self.get_property_sink_pad(str, "key")
        if not key_sink:
            key_sink = pad.PropertySinkPad(
                id="key",
                group="key",
                owner_node=self,
                default_type_constraints=[pad_constraints.String()],
                value="",
            )

        value_source = self.get_property_source_pad(str, "value")
        if not value_source:
            value_source = pad.PropertySourcePad(
                id="value",
                owner_node=self,
                group="value",
                default_type_constraints=[pad_constraints.String()],
                value="",
            )

        sink.link_types_to_pad(source)

        self.pads = [key_sink, sink, value_source, source]

    async def run(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        key_pad = self.get_property_sink_pad_required(str, "key")
        value_pad = self.get_property_source_pad_required(str, "value")

        async for item in sink:
            if item is None:
                continue

            md = item.ctx.publisher_metadata
            if md is None:
                if value_pad.get_value() != "":
                    value_pad.push_item("", item.ctx)
            else:
                new_value = md.get(key_pad.get_value(), "")

                if value_pad.get_value() != new_value:
                    value_pad.push_item(new_value, item.ctx)

            source.push_item(item.value, item.ctx)
            item.ctx.complete()
