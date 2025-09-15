# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import os
import aiofiles
import yaml
import logging
from .mcp_server_config import MCPServerConfig


class MCPServerProvider:
    def __init__(self):
        self.mcp_config_file = os.environ.get("GABBER_MCP_CONFIG", "mcp.yaml")

    async def get_config(self) -> MCPServerConfig:
        async with aiofiles.open(self.mcp_config_file, mode="r") as f:
            content = await f.read()
            config_dict = yaml.safe_load(content)
            return MCPServerConfig.model_validate(config_dict)
