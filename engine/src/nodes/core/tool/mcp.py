# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast

from core import node, pad
from core.node import NodeMetadata


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

        mcp_server = cast(pad.PropertySinkPad, self.get_pad("mcp_server"))
        if not mcp_server:
            mcp_server = pad.PropertySinkPad(
                id="mcp_server",
                group="config",
                owner_node=self,
                default_type_constraints=[
                    pad.types.Enum(options=[s.name for s in self.mcp_servers])
                ],
                value=self.mcp_servers[0].name if self.mcp_servers else None,
            )

        self.pads = [self_pad, mcp_server]

    async def run(self):
        pass

    async def generate_mcp_server(self):
        pass
