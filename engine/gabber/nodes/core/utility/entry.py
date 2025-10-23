# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

from gabber.core import pad
from gabber.core.types import runtime
from gabber.core.node import Node, NodeMetadata
from gabber.core.types import pad_constraints


class Entry(Node):
    def resolve_pads(self):
        trigger = cast(pad.StatelessSourcePad, self.get_pad("trigger"))
        if not trigger:
            trigger = pad.StatelessSourcePad(
                id="trigger",
                group="trigger",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )
            self.pads.append(trigger)

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="utility", tags=["trigger", "start"]
        )

    async def run(self):
        trigger = cast(pad.StatelessSourcePad, self.get_pad_required("trigger"))

        # Wait a bit to make sure the clients are ready
        await asyncio.sleep(0.5)
        trigger.push_item(
            runtime.Trigger(), pad.RequestContext(parent=None, metadata=None)
        )
