# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast
import re

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

    def fix_tools(self):
        tool_pad = cast(pad.PropertySinkPad[dict[str, Any]], self.get_pad("config"))
        config_value = tool_pad.get_value()
        tools: list[dict[str, Any]] = config_value.get("tools", [])

        if not tools:
            return

        seen_names: set[str] = set()
        valid_tools: list[dict[str, Any]] = []

        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                logging.warning(f"Skipping invalid tool entry (not a dict): {tool}")
                continue

            name = tool.get("name")
            if not name or not isinstance(name, str) or name.strip() == "":
                base_name = tool.get("description", "unnamed_tool").strip()
                if not base_name:
                    base_name = "tool"

                sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", base_name)[:50]
                if not sanitized or sanitized[0].isdigit():
                    sanitized = "tool_" + sanitized
                name = sanitized or f"tool_{i}"

            name = name.strip()

            original_name = name
            suffix = 1
            while name in seen_names:
                name = f"{original_name}_{suffix}"
                suffix += 1

            seen_names.add(name)
            tool["name"] = name

            if "description" not in tool or not isinstance(
                tool.get("description"), str
            ):
                tool["description"] = tool.get("description", f"Tool: {name}")

            if "parameters" not in tool:
                tool["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }

            if "destination" not in tool:
                tool["destination"] = {"type": "client"}

            valid_tools.append(tool)

        config_value["tools"] = valid_tools

        logging.info(
            f"ToolGroup '{self.id}' fixed tools: {len(valid_tools)} valid, "
            f"{len(tools) - len(valid_tools)} removed/invalid"
        )

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
