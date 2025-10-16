# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from gabber.core import node, pad
from gabber.core.node import NodeMetadata
from gabber.core.types import pad_constraints


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
                default_type_constraints=[pad_constraints.String()],
                value="",
            )
            self.pads.append(text)

        # Persisted layout width for comment node (in pixels)
        width = self.get_pad("width")
        if not width:
            width = pad.PropertySinkPad(
                id="width",
                owner_node=self,
                group="layout",
                default_type_constraints=[
                    pad_constraints.Integer(minimum=160, maximum=1600)
                ],
                value=480,
            )
            self.pads.append(width)
