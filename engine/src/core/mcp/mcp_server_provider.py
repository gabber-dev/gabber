# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from abc import ABC, abstractmethod

from .mcp_server_config import MCPServerConfig


class MCPServerProvider(ABC):
    @abstractmethod
    async def get_config(self) -> MCPServerConfig:
        """List all mcp server configs."""
        pass
