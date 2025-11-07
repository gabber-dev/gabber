# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio

from gabber.core import pad
from gabber.core.node import Node
from gabber.core.types import runtime
from gabber.core.node import NodeMetadata
from gabber.core.types import pad_constraints


class VisemeDebug(Node):
    @classmethod
    def get_description(cls) -> str:
        return "A node for debugging viseme lip sync data."

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="debug", tags=["viseme"])

    def resolve_pads(self):
        viseme = self.get_stateless_sink_pad(runtime.Viseme, "viseme")
        if not viseme:
            viseme = pad.StatelessSinkPad(
                id="viseme",
                owner_node=self,
                default_type_constraints=[pad_constraints.Viseme()],
                group="viseme",
            )

        self.pads = [viseme]

    async def run(self):
        viseme = self.get_stateless_sink_pad_required(runtime.Viseme, "viseme")

        async def viseme_consume():
            async for item in viseme:
                self.logger.info(f"Viseme Frame: {item.value.value}")
                item.ctx.complete()

        try:
            await asyncio.gather(viseme_consume())
        except Exception as e:
            print(f"Error in OutputNode: {e}")
