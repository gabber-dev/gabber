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

    def resolve_pads(self):
        if not self.get_pad("trigger"):
            self.pads.append(
                pad.StatelessSourcePad(
                    id="trigger",
                    owner_node=self,
                    group="trigger",
                    default_type_constraints=[pad.types.Trigger()],
                )
            )
