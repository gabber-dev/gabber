# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast
import jsonschema

from gabber.core import node, pad
from gabber.core.types import runtime, client, pad_constraints, mapper
from gabber.core.node import NodeMetadata


DEFAULT_TOOLS = [
    runtime.ToolDefinition(
        name="get_weather",
        description="Get the current weather for a given location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get the weather for",
                }
            },
            "required": ["location"],
        },
        destination=runtime.ToolDefinitionDestination_Client(),
    )
]

DEFAULT_RETRY_POLICY = runtime.ToolDefinitionDestination_Webhook_RetryPolicy(
    max_retries=3, backoff_factor=2.0, initial_delay_seconds=1.0
)

DEFAULT_CONFIG = {"tools": [tool.model_dump() for tool in DEFAULT_TOOLS]}


class ToolGroup(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Groups multiple tools together for use with LLMs"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="tools", tags=["collection", "group"]
        )

    def resolve_pads(self):
        self_pad = cast(pad.PropertySourcePad, self.get_pad("self"))
        if not self_pad:
            self_pad = pad.PropertySourcePad(
                id="self",
                group="self",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.NodeReference(node_types=["ToolGroup"])
                ],
                value=runtime.NodeReference(node_id=self.id),
            )

        config = cast(pad.PropertySinkPad, self.get_pad("config"))
        if not config:
            config = pad.PropertySinkPad(
                id="config",
                owner_node=self,
                default_type_constraints=[pad_constraints.Object()],
                group="config",
                value=DEFAULT_CONFIG,
            )

        self.pads = [config, self_pad]
        self.resolve_enabled_pads()

    def resolve_enabled_pads(self):
        config_pad = cast(pad.PropertySinkPad[dict[str, Any]], self.get_pad("config"))
        self_pad = cast(pad.PropertySourcePad, self.get_pad("self"))
        tools = config_pad.get_value().get("tools", [])
        sanitized_tools: list[dict[str, Any]] = []
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            name = tool.get("name")
            if not name or not isinstance(name, str):
                continue

            parameters = tool.get("parameters")
            if not parameters or not isinstance(parameters, dict):
                continue

            try:
                jsonschema.validate(
                    instance=parameters,
                    schema={
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "properties": {"type": "object"},
                            "required": {"type": "array"},
                        },
                        "required": ["type", "properties", "required"],
                    },
                )
            except jsonschema.ValidationError as e:
                self.logger.warning(
                    f"ToolGroup '{self.id}' tool '{name}' has invalid parameters schema: {str(e)}"
                )
                continue

            sanitized_tools.append(tool)

        tool_pads: list[pad.PropertySinkPad] = []
        for tool in sanitized_tools:
            pad_id = f"{tool['name']}"
            if not self.get_pad(pad_id):
                tool_pad = pad.PropertySinkPad(
                    id=pad_id,
                    group=pad_id,
                    owner_node=self,
                    default_type_constraints=[pad_constraints.Boolean()],
                    value=True,
                )
                tool_pads.append(tool_pad)
            else:
                tool_pads.append(cast(pad.PropertySinkPad, self.get_pad(pad_id)))

        self.pads = cast(list[pad.Pad], [config_pad, self_pad] + tool_pads)

    # TODO
    def has_tool(self, tool_name: str) -> bool:
        return False

    def list_tool_definitions(self):
        config_pad = cast(pad.PropertySinkPad[dict[str, Any]], self.get_pad("config"))
        tools = config_pad.get_value().get("tools", [])
        res: list[runtime.ToolDefinition] = []
        for t in tools:
            if not isinstance(t, dict):
                continue

            enabled_pad = cast(pad.PropertySinkPad, self.get_pad(t.get("name", "")))
            if not enabled_pad or not enabled_pad.get_value():
                continue

            try:
                client_def = client.ToolDefinition.model_validate(t)
                runtime_def = mapper.Mapper.client_to_runtime(client_def)
                if isinstance(runtime_def, runtime.ToolDefinition):
                    res.append(runtime_def)
            except Exception as e:
                self.logger.warning(
                    f"ToolGroup '{self.id}' has invalid tool definition: {str(e)}"
                )
                continue

        return res

    # TODO
    async def call_tools(
        self,
        tool_calls: list[runtime.ToolCall],
        ctx: pad.RequestContext,
        timeout: float = 30.0,  # Added timeout parameter with default
    ) -> list[str]:
        tasks: list[asyncio.Task[str]] = []
        results: list[str] = []
        return results

    async def _safe_tool_call(
        self,
        tool: Any,  # Replace with actual tool type
        tc: runtime.ToolCall,
        ctx: pad.RequestContext,
    ) -> str:
        try:
            res = await tool.call_tool(tc, ctx)
            return res
        except asyncio.CancelledError:
            return f"Tool '{tc.name}' cancelled"
        except Exception as e:
            logging.error(f"Error in tool '{tc.name}': {str(e)}")
            return f"Tool '{tc.name}' failed: {str(e)}"
