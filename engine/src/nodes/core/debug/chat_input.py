# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from core import node, pad
from core.node import NodeMetadata


class ChatInput(node.Node):
    type = "ChatInput"

    @classmethod
    def get_description(cls) -> str:
        return "A chat input node to send text into your Gabber flow"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="debug", tags=["input", "text"])

    def resolve_pads(self):
        output = cast(pad.StatelessSourcePad | None, self.get_pad("output"))
        if output is None:
            output = pad.StatelessSourcePad(
                id="output",
                owner_node=self,
                group="text",
                type_constraints=[pad.types.String()],
            )
            self.pads.append(output)

    async def run(self):
        pass
