# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast

from core import node, pad, runtime_types
from core.node import NodeMetadata
from core.runtime_types import ToolCall


class Tool(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Defines a tool that can be triggered by user inputs"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="tools", tags=["function", "definition"]
        )

    async def resolve_pads(self):
        self_pad = cast(pad.PropertySourcePad, self.get_pad("self"))
        if not self_pad:
            self_pad = pad.PropertySourcePad(
                id="self",
                group="self",
                owner_node=self,
                type_constraints=[pad.types.NodeReference(node_types=["Tool"])],
                value=self,
            )
            self.pads.append(self_pad)

        name = cast(pad.PropertySinkPad, self.get_pad("name"))
        if not name:
            name = pad.PropertySinkPad(
                id="name",
                owner_node=self,
                group="name",
                type_constraints=[pad.types.String(max_length=100)],
                value="get_weather",
            )
            self.pads.append(name)

        description = cast(pad.PropertySinkPad, self.get_pad("description"))
        if not description:
            description = pad.PropertySinkPad(
                id="description",
                group="description",
                owner_node=self,
                type_constraints=[pad.types.String(max_length=500)],
                value="Get the current weather for a specified location.",
            )
            self.pads.append(description)

        schema_pad = cast(pad.PropertySinkPad, self.get_pad("schema"))
        if not schema_pad:
            schema_pad = pad.PropertySinkPad(
                id="schema",
                group="schema",
                owner_node=self,
                type_constraints=[pad.types.Schema()],
                value=runtime_types.Schema(properties={"location": pad.types.String()}),
            )
            self.pads.append(schema_pad)

        schema = cast(runtime_types.Schema, schema_pad.get_value())
        if not schema:
            schema = runtime_types.Schema(properties={})
        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                group="source",
                owner_node=self,
                type_constraints=[
                    pad.types.Object(object_schema=schema.to_json_schema())
                ],
            )
            self.pads.append(source)

        source.set_type_constraints(
            [pad.types.Object(object_schema=schema.to_json_schema())]
        )

    def get_tool_definition(self) -> runtime_types.ToolDefinition:
        name = cast(pad.PropertySinkPad, self.get_pad_required("name"))
        description = cast(pad.PropertySinkPad, self.get_pad_required("description"))
        schema = cast(pad.PropertySinkPad, self.get_pad_required("schema"))
        td = runtime_types.ToolDefinition(
            name=name.get_value(),
            description=description.get_value(),
            parameters=schema.get_value() or None,
        )
        return td

    async def call_tool(self, tool_call: ToolCall, ctx: pad.RequestContext):
        source = cast(pad.StatelessSourcePad, self.get_pad_required("source"))
        fut = asyncio.Future[str]()

        def on_tool_call_done(results: list[Any]) -> None:
            all_results: list[str] = []
            for result in results:
                if not isinstance(result, str):
                    logging.warning(
                        f"Tool call result is not a string: {result}. "
                        "Converting to string."
                    )
                    continue
                all_results.append(result)

            fut.set_result(" | ".join(all_results))

        new_ctx = pad.RequestContext(parent=ctx, originator="tool_call")
        new_ctx.add_done_callback(on_tool_call_done)
        # TODO validate schema
        source.push_item(tool_call.arguments, new_ctx)
        ctx.complete()
        res = await fut
        return res

    def get_name(self) -> str:
        name_pad = cast(pad.PropertySinkPad, self.get_pad_required("name"))
        return name_pad.get_value()
