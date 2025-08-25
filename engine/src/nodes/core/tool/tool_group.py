# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast

from core import node, pad, runtime_types
from core.node import NodeMetadata

from nodes.core.tool import Tool


class ToolGroup(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Groups multiple tools together for use with LLMs"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="tools", tags=["collection", "group"]
        )

    @property
    def tool_nodes(self):
        res: list[Tool] = []
        for p in self.pads:
            if not isinstance(p, pad.PropertySinkPad):
                continue

            if p.get_group() != "tool":
                continue

            if not p.get_value():
                continue

            if not isinstance(p.get_value(), Tool):
                raise TypeError(
                    f"Expected Tool instance, got {p.get_value()} for pad {p.get_id()}"
                )
            res.append(p.get_value())
        return res

    def resolve_pads(self):
        self_pad = cast(pad.PropertySourcePad, self.get_pad("self"))
        if not self_pad:
            self_pad = pad.PropertySourcePad(
                id="self",
                group="self",
                owner_node=self,
                default_type_constraints=[
                    pad.types.NodeReference(node_types=["ToolGroup"])
                ],
                value=self,
            )

        num_tools = cast(pad.PropertySinkPad, self.get_pad("num_tools"))
        if not num_tools:
            num_tools = pad.PropertySinkPad(
                id="num_tools",
                owner_node=self,
                default_type_constraints=[pad.types.Integer()],
                group="num_tools",
                value=1,
            )

        tools: list[pad.Pad] = []
        for i in range(num_tools.get_value() or 1):
            pad_id = f"tool_{i}"
            tp = self.get_pad(pad_id)
            if not tp:
                tp = pad.PropertySinkPad(
                    id=pad_id,
                    owner_node=self,
                    default_type_constraints=[
                        pad.types.NodeReference(node_types=["Tool"])
                    ],
                    group="tool",
                    value=None,
                )
            tools.append(tp)

        self.pads = [num_tools, self_pad] + tools

    async def call_tools(
        self,
        tool_calls: list[runtime_types.ToolCall],
        ctx: pad.RequestContext,
        timeout: float = 30.0,  # Added timeout parameter with default
    ) -> list[str]:
        tasks: list[asyncio.Task[str]] = []
        results: list[str] = []

        for tc in tool_calls:
            found_tool = False
            for tool in self.tool_nodes:
                if tool.get_name() == tc.name:
                    task = asyncio.create_task(self._safe_tool_call(tool, tc, ctx))
                    tasks.append(task)
                    found_tool = True
                    break

            if not found_tool:
                logging.warning(
                    f"Tool call '{tc.name}' not found in ToolGroup '{self.id}'."
                )
                tasks.append(
                    asyncio.create_task(
                        asyncio.sleep(0, result=f"Tool '{tc.name}' not found.")
                    )
                )

        try:
            done, pending = await asyncio.wait(
                tasks, timeout=timeout, return_when=asyncio.ALL_COMPLETED
            )

            for task in done:
                try:
                    results.append(await task)
                except asyncio.CancelledError:
                    results.append(f"Tool call cancelled: {task.get_name()}")
                except Exception as e:
                    results.append(f"Tool call failed: {str(e)}")

            for task in pending:
                task.cancel()
                results.append(f"Tool call timed out after {timeout}s")

            while len(results) < len(tool_calls):
                results.append("Unknown error: Result missing")

        except Exception as e:
            logging.error(f"Error in call_tools: {str(e)}")
            results = [f"System error: {str(e)}"] * len(tool_calls)

        return results

    async def _safe_tool_call(
        self,
        tool: Any,  # Replace with actual tool type
        tc: runtime_types.ToolCall,
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
