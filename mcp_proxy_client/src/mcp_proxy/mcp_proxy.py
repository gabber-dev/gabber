import asyncio
import logging
from contextlib import AsyncExitStack
import anyio

import mcp
from gabber import (
    MCPServer,
    MCPTransportDatachannelProxy,
    MCPTransportSSE,
    MCPTransportSTDIO,
)
from livekit import rtc
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.shared.message import SessionMessage
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from .datachannel_transport import datachannel_client_proxy

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MCPProxy:
    def __init__(self, *, room: rtc.Room, server: MCPServer):
        self.room = room
        self.server = server
        self.session: mcp.ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.proxy_task: asyncio.Task | None = None

    async def run(self):
        if isinstance(self.server.transport, MCPTransportDatachannelProxy):
            logger.info(f"Starting MCPProxy for {self.server}")
            local_transport = self.server.transport.local_transport
            read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
            write_stream: MemoryObjectSendStream[SessionMessage]
            if isinstance(local_transport, MCPTransportSSE):
                read_stream, write_stream = await self.exit_stack.enter_async_context(
                    sse_client("http://localhost:9876")
                )
            elif isinstance(local_transport, MCPTransportSTDIO):
                read_stream, write_stream = await self.exit_stack.enter_async_context(
                    stdio_client(
                        mcp.StdioServerParameters(
                            command=local_transport.command, args=local_transport.args
                        )
                    )
                )
            else:
                raise ValueError(f"Unsupported local transport: {local_transport}")
            self.session = await self.exit_stack.enter_async_context(
                mcp.ClientSession(read_stream=read_stream, write_stream=write_stream)
            )
            # self.proxy_task = asyncio.create_task(
            #     datachannel_client_proxy(
            #         room=self.room,
            #         mcp_name=self.server.name,
            #         other_read_stream=read_stream,
            #         other_write_stream=write_stream,
            #     )
            # )
            logger.info(f"Initializing mcp session for: {self.server.name}")
            await self.session.initialize()
            logger.info(f"MCPProxy session initialized for {self.server.name}")
            prompts = await self.session.list_prompts()
            logger.info(f"MCPProxy prompts for {self.server.name}: {prompts}")
            tools = await self.session.list_tools()
            logger.info(f"MCPProxy tools for {self.server.name}: {tools}")
            # await self.proxy_task
            logger.info(f"MCPProxy finished {self.server.name}")

    async def aclose(self):
        await self.exit_stack.aclose()
        if self.proxy_task:
            self.proxy_task.cancel()
            try:
                await self.proxy_task
            except asyncio.CancelledError:
                pass
