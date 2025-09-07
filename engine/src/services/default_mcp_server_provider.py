# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from core import mcp
import os
import aiofiles
import yaml
import logging


class DefaultMCPServerProvider(mcp.MCPServerProvider):
    def __init__(self):
        self.mcp_config_file = os.environ["GABBER_MCP_CONFIG"]

    async def get_config(self) -> mcp.MCPServerConfig:
        async with aiofiles.open(self.mcp_config_file, mode="r") as f:
            content = await f.read()
            logging.info(
                f"NEIL Loaded MCP config from {self.mcp_config_file} - {content}"
            )
            config_dict = yaml.safe_load(content)
            logging.info(f"NEIL Parsed MCP config: {config_dict}")
            return mcp.MCPServerConfig.model_validate(config_dict)
