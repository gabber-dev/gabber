# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast

from gabber.core import node, pad
from gabber.core.types import runtime
from gabber.core.node import NodeMetadata
from gabber.core.types.runtime import ToolCall


class Tool(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Defines a tool that can be triggered by user inputs"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="tools", tags=["function", "definition"]
        )

    def resolve_pads(self):
        self_pad = cast(pad.PropertySourcePad, self.get_pad("self"))
        if not self_pad:
            self_pad = pad.PropertySourcePad(
                id="self",
                group="self",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.NodeReference(node_types=["Tool"])
                ],
                value=self,
            )

        name = cast(pad.PropertySinkPad, self.get_pad("name"))
        if not name:
            name = pad.PropertySinkPad(
                id="name",
                owner_node=self,
                group="name",
                default_type_constraints=[pad_constraints.String(max_length=100)],
                value="get_weather",
            )

        description = cast(pad.PropertySinkPad, self.get_pad("description"))
        if not description:
            description = pad.PropertySinkPad(
                id="description",
                group="description",
                owner_node=self,
                default_type_constraints=[pad_constraints.String(max_length=500)],
                value="Get the current weather for a specified location.",
            )

        schema_pad = cast(pad.PropertySinkPad, self.get_pad("schema"))
        if not schema_pad:
            schema_pad = pad.PropertySinkPad(
                id="schema",
                group="schema",
                owner_node=self,
                default_type_constraints=[pad_constraints.Schema()],
                value=runtime.Schema(properties={"location": pad_constraints.String()}),
            )

        schema = cast(runtime.Schema, schema_pad.get_value())
        if not schema:
            schema = runtime.Schema(properties={})
        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                group="source",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.Object(object_schema=schema.to_json_schema())
                ],
            )

        source.set_default_type_constraints(
            [pad_constraints.Object(object_schema=schema.to_json_schema())]
        )
        self.pads = [self_pad, name, description, schema_pad, source]

    def get_tool_definition(self) -> runtime.ToolDefinition:
        name = cast(pad.PropertySinkPad, self.get_pad_required("name"))
        description = cast(pad.PropertySinkPad, self.get_pad_required("description"))
        schema = cast(pad.PropertySinkPad, self.get_pad_required("schema"))
        td = runtime.ToolDefinition(
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
