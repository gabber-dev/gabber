# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast

from gabber.core import node, pad
from gabber.core.types import runtime
from gabber.core.node import NodeMetadata

from gabber.core.types import pad_constraints

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

    def fix_tools(self):
        tool_pad = cast(pad.PropertySinkPad[dict[str, Any]], self.get_pad("config"))
        tools = tool_pad.get_value().get("tools", [])
        for tool in tools:
            name = tool.get("name")
            if not name:
                tool["name"] = "unnamed_tool"

    def resolve_enabled_pads(self):
        tool_pad = cast(pad.PropertySinkPad[dict[str, Any]], self.get_pad("tools"))
        tools = tool_pad.get_value().get("tools", [])
        for tool in tools:
            name = tool.get("name")

    # TODO
    def has_tool(self, tool_name: str) -> bool:
        return False

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
