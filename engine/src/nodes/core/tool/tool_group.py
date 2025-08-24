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
                type_constraints=[pad.types.NodeReference(node_types=["ToolGroup"])],
                value=self,
            )
            self.pads.append(self_pad)

        connected_tool_pads: list[pad.Pad] = []
        for p in self.pads:
            if not isinstance(p, pad.PropertySinkPad):
                continue
            if p.get_value() is not None and p.get_id().startswith("tool_"):
                connected_tool_pads.append(p)

        connected_tool_pads.sort(key=lambda x: int(x.get_id().split("_")[1]))
        biggest_index = 0
        if connected_tool_pads:
            biggest_index = int(connected_tool_pads[-1].get_id().split("_")[1])

        next_index = biggest_index + 1
        free_pad = pad.PropertySinkPad(
            id=f"tool_{next_index}",
            group="tool",
            owner_node=self,
            type_constraints=[pad.types.NodeReference(node_types=["Tool"])],
            value=None,
        )

        # Rebuild pads list with renumbered connected pads, one free pad, and self pad
        self.pads = connected_tool_pads + [free_pad] + [self_pad]

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
