# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from core import node, pad
from core.node import NodeMetadata


class Comment(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "A comment node for adding notes and documentation to your graph"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core",
            secondary="utility",
            tags=["documentation", "comment"],
        )

    def resolve_pads(self):
        text = self.get_pad("text")
        if not text:
            text = pad.PropertySinkPad(
                id="text",
                owner_node=self,
                group="text",
                type_constraints=[pad.types.String()],
                value="",
            )
            self.pads.append(text)
