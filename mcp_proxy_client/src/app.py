# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging

from gabber import ConnectionState, Engine, MCPServer
from livekit import rtc

from connection import ConnectionProvider

from mcp_proxy import MCPProxy

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class App:
    def __init__(self, *, connection_provider: ConnectionProvider, run_id: str):
        self.run_id = run_id
        self.engine = Engine(on_connection_state_change=self.on_connection_state_change)
        self.connection_provider = connection_provider

    async def run(self):
        dets = await self.connection_provider.get_connection(run_id=self.run_id)
        proxy_supervisor = ProxySupervisor(room=self.engine._livekit_room)

        await self.engine.connect(connection_details=dets)
        mcp_servers = await self.engine.list_mcp_servers()
        for s in mcp_servers:
            proxy_supervisor.add_server(s)

        await proxy_supervisor.wait_all()

    def on_connection_state_change(self, state: ConnectionState):
        logger.info(f"Connection state changed: {state}")


class ProxySupervisor:
    def __init__(self, *, room: rtc.Room):
        self.tasks: list[asyncio.Task] = []
        self.room = room
        self._closed = False

    def add_server(self, server: MCPServer):
        self.tasks.append(asyncio.create_task(self._supervise_server(server)))

    async def _supervise_server(self, server: MCPServer):
        while not self._closed:
            proxy = MCPProxy(room=self.room, server=server)
            try:
                await proxy.run()
            except Exception as e:
                logger.error(f"Error in MCPProxy: {e}", exc_info=True)
            await asyncio.sleep(2)

    async def wait_all(self):
        await asyncio.gather(*self.tasks)

    async def aclose(self):
        self._closed = True
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
