# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from core import mcp
import logging
import os
import aiofiles
import datetime


class DefaultMCPServerProvider(mcp.MCPServerProvider):
    def __init__(self):
        self.secret_file = os.environ["GABBER_MCP_CONFIG"]

    async def list_servers(self) -> list[mcp.MCPServer]:
        pass

    async def _read_secrets(self) -> dict[str, str]:
        secrets = {}
        if not os.path.exists(self.secret_file):
            logging.warning(f"Secret file {self.secret_file} does not exist.")
            return {}

        async with aiofiles.open(self.secret_file, mode="r") as f:
            async for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    secrets[key] = value
        return secrets
