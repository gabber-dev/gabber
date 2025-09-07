# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast

from core import node, pad, runtime_types
from core.node import NodeMetadata
from core.runtime_types import ToolCall


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
                default_type_constraints=[pad.types.NodeReference(node_types=["MCP"])],
                value=self,
            )

        proxy_token = cast(pad.PropertySourcePad, self.get_pad("proxy_token"))
        if not proxy_token:
            proxy_token = pad.PropertySourcePad(
                id="proxy_token",
                group="config",
                owner_node=self,
                default_type_constraints=[pad.types.String()],
                value="",
            )

    async def run(self):
        pass

    async def generate_proxy_token(self):
        pass
