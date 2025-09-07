# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from abc import ABC, abstractmethod

from .mcp_server_config import MCPServer


class MCPServerProvider(ABC):
    @abstractmethod
    async def list_servers(self) -> list[MCPServer]:
        """List all mcp server configs."""
        pass
