# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

from core import pad, runtime_types
from core.node import Node, NodeMetadata


class PortalSourceStart(Node):
    def resolve_pads(self):
        sink = cast(pad.SinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                group="sink",
                owner_node=self,
                default_type_constraints=None,
            )

        self_pad = cast(pad.PropertySourcePad, self.get_pad("self"))
        if not self_pad:
            self_pad = pad.PropertySourcePad(
                id="self",
                group="self",
                owner_node=self,
                default_type_constraints=[
                    pad.types.NodeReference(node_types=["PortalSourceStart"])
                ],
                value=self,
            )

        self.pads = [sink, self_pad]

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="utility", tags=["trigger", "start"]
        )

    async def run(self):
        trigger = cast(pad.StatelessSourcePad, self.get_pad_required("trigger"))

        # Wait a bit to make sure the clients are ready
        await asyncio.sleep(0.5)
        trigger.push_item(runtime_types.Trigger(), pad.RequestContext(parent=None))
