# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast
import contextlib

from gabber.core import node, pad, mcp
from gabber.core.types import runtime
from gabber.core.node import NodeMetadata
from mcp.types import ContentBlock
from mcp import ClientSession
from gabber.core.types import pad_constraints


class MCP(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Defines an MCP client"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="tools", tags=["function", "mcp"])

    def resolve_pads(self):
        self_pad = cast(pad.PropertySourcePad, self.get_pad("self"))
        if not self_pad:
            self_pad = pad.PropertySourcePad(
                id="self",
                group="self",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.NodeReference(node_types=["MCP"])
                ],
                value=runtime.NodeReference(node_id=self.id),
            )

        mcp_server = cast(pad.PropertySinkPad, self.get_pad("mcp_server"))
        if not mcp_server:
            mcp_server = pad.PropertySinkPad(
                id="mcp_server",
                group="config",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.String(),
                ],
                value=None,
            )

        self.pads = [self_pad, mcp_server]

    async def run(self):
        self.init_lock = asyncio.Lock()
        self.session: ClientSession | None = None
        while True:
            exit_stack = contextlib.AsyncExitStack()
            async with self.init_lock:
                self.session = await self.create_session(exit_stack)
                try:
                    await asyncio.wait_for(self.session.initialize(), timeout=2)
                    await asyncio.sleep(1)
                except asyncio.TimeoutError:
                    logging.error("MCP Client session timeout")
                    await exit_stack.aclose()
                    continue

            try:
                await self.session_ping_loop(self.session)
            except Exception as e:
                logging.error(f"MCP Client list_tools error: {e}")
                await exit_stack.aclose()
                continue

    async def create_session(self, exit_stack: contextlib.AsyncExitStack):
        mcp_server_pad = cast(pad.PropertySinkPad, self.get_pad("mcp_server"))
        if not mcp_server_pad or not mcp_server_pad.get_value():
            raise ValueError("MCP server pad not configured")

        mcp_server_name = mcp_server_pad.get_value()
        assert isinstance(mcp_server_name, str)

        self.logger.info(f"Connecting to MCP server '{mcp_server_name}'")
        read_stream, write_stream = await exit_stack.enter_async_context(
            mcp.datachannel_host(self.room, "mcp_proxy", mcp_server_name)
        )
        session = await exit_stack.enter_async_context(
            ClientSession(read_stream=read_stream, write_stream=write_stream)
        )
        return session

    async def session_ping_loop(self, session: ClientSession):
        try:
            while True:
                await asyncio.sleep(10)
                await asyncio.wait_for(session.send_ping(), timeout=2)
        except asyncio.CancelledError:
            self.logger.info("MCP Client ping loop cancelled")
            raise

    async def to_tool_definitions(self) -> list[runtime.ToolDefinition]:
        async with self.init_lock:
            if not self.session:
                raise ValueError("MCP session not initialized")
            mcp_tools_res = await self.session.list_tools()
            mcp_tools = mcp_tools_res.tools
            tool_defs: list[runtime.ToolDefinition] = []
            for t in mcp_tools:
                tool_def = runtime.ToolDefinition(
                    name=t.name,
                    description=t.description or "",
                    parameters=t.inputSchema,
                    destination=runtime.ToolDefinitionDestination_Client(),
                )
                tool_defs.append(tool_def)

            return tool_defs

    async def call_tool(self, tool_call: runtime.ToolCall):
        self.logger.info(f"MCP Client calling tool '{tool_call.name}'")
        sess: ClientSession
        async with self.init_lock:
            if not self.session:
                raise ValueError("MCP session not initialized")
            sess = self.session

        results: list[ContentBlock] | Exception = []
        try:
            response = await asyncio.wait_for(
                sess.call_tool(tool_call.name, tool_call.arguments), timeout=15
            )
            results = response.content if response.content else []
        except asyncio.TimeoutError:
            results = Exception(f"Tool call '{tool_call.name}' timed out.")
        except Exception as e:
            results = Exception(f"Error calling tool '{tool_call.name}': {e}")

        return results
