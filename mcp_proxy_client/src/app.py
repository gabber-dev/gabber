# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging

from gabber import ConnectionState, Engine

from connection import ConnectionProvider

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class App:
    def __init__(self, *, connection_provider: ConnectionProvider, run_id: str):
        self.run_id = run_id
        self.engine = Engine(on_connection_state_change=self.on_connection_state_change)
        self.connection_provider = connection_provider

    async def run(self):
        dets = await self.connection_provider.get_connection(run_id=self.run_id)

        await self.engine.connect(connection_details=dets)
        mcp_servers = await self.engine.list_mcp_servers()
        logger.info(f"NEIL MCP Servers: {mcp_servers}")
        while True:
            await asyncio.sleep(1)

    def on_connection_state_change(self, state: ConnectionState):
        logger.info(f"Connection state changed: {state}")
