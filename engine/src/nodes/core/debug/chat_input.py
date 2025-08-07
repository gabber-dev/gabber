# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from core import node, pad
from core.node import NodeMetadata


class ChatInput(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "A chat input node to send text into your Gabber flow"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core",
            secondary="debug",
            tags=["input", "text"]
        )

    async def resolve_pads(self):
        output = cast(pad.StatelessSourcePad, self.get_pad("output"))
        if not output:
            self.pads.append(
                pad.StatelessSourcePad(
                    id="output",
                    owner_node=self,
                    group="text",
                    type_constraints=[pad.types.String()],
                )
            )

    async def run(self):
        # The actual message sending is handled by the frontend component
        # This node just provides the output pad for the messages
        pass