# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from core import node, pad
from core.node import NodeMetadata


class ButtonTrigger(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Manually activate a trigger to run an action"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="utility", tags=["trigger", "debug"]
        )

    async def resolve_pads(self):
        trigger = self.get_pad("trigger")
        if not trigger:
            trigger = pad.StatelessSourcePad(
                id="trigger",
                group="trigger",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )

        self.pads = [trigger]
