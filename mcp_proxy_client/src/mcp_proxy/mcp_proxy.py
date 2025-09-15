import asyncio
import logging
from contextlib import AsyncExitStack

import mcp
from livekit import rtc
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.shared.message import SessionMessage
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from .mcp_server_config import (
    MCPServer,
    MCPTransportSSE,
    MCPTransportSTDIO,
)

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
        logger.info(f"Starting MCPProxy for {self.server}")
        transport = self.server.transport
        read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
        write_stream: MemoryObjectSendStream[SessionMessage]
        if isinstance(transport, MCPTransportSSE):
            read_stream, write_stream = await self.exit_stack.enter_async_context(
                sse_client("http://localhost:9876")
            )
        elif isinstance(transport, MCPTransportSTDIO):
            read_stream, write_stream = await self.exit_stack.enter_async_context(
                stdio_client(
                    mcp.StdioServerParameters(
                        command=transport.command,
                        args=transport.args,
                        cwd=transport.cwd,
                        env=transport.env,
                    )
                )
            )
        else:
            raise ValueError(f"Unsupported local transport: {transport}")

        await datachannel_client_proxy(
            room=self.room,
            mcp_name=self.server.name,
            other_read_stream=read_stream,
            other_write_stream=write_stream,
        )

        logger.info(f"MCPProxy finished {self.server.name}")

    async def aclose(self):
        await self.exit_stack.aclose()
        if self.proxy_task:
            self.proxy_task.cancel()
            try:
                await self.proxy_task
            except asyncio.CancelledError:
                pass
