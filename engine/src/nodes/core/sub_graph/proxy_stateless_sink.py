# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import cast

from core import node, pad
from core.node import NodeMetadata
from utils import short_uuid


class ProxyStatelessSink(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Create a stateless sink pad that is exposed when using your subgraph in a flow"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="subgraph", secondary="proxy", tags=["sink", "stateless"]
        )

    async def resolve_pads(self):
        proxy_pad = cast(pad.StatelessSourcePad, self.get_pad("proxy"))
        if not proxy_pad:
            self.pads.append(
                pad.StatelessSourcePad(
                    id="proxy",
                    owner_node=self,
                    group="proxy",
                    type_constraints=None,
                )
            )
            proxy_pad = cast(pad.StatelessSourcePad, self.get_pad("proxy"))

        pad_id = cast(pad.PropertySinkPad, self.get_pad("pad_id"))
        if not pad_id:
            self.pads.append(
                pad.PropertySinkPad(
                    id="pad_id",
                    owner_node=self,
                    group="pad_id",
                    type_constraints=[pad.types.String()],
                    value=f"proxy_{short_uuid()}",
                )
            )
            pad_id = cast(pad.PropertySinkPad, self.get_pad("pad_id"))
        tsc = None
        nps = proxy_pad.get_next_pads()
        if len(nps) > 1:
            for np in nps[1:]:
                proxy_pad.disconnect(np)
            logging.error(
                f"ProxyStatelessSink has multiple next pads: {proxy_pad.get_id()}. Please ensure only one next pad is connected."
            )
        for np in nps:
            np = cast(pad.StatelessSinkPad, np)
            tsc = pad.types.INTERSECTION(tsc, np.get_type_constraints())

        proxy_pad.set_type_constraints(tsc)

    def get_pad_id(self) -> str:
        pad_id = cast(pad.PropertySinkPad, self.get_pad_required("pad_id"))
        return pad_id.get_value()

    def get_proxy_target_pads(self) -> list[pad.StatelessSinkPad]:
        proxy_pad = cast(pad.StatelessSourcePad, self.get_pad_required("proxy"))
        nps = proxy_pad.get_next_pads()
        if not nps:
            return []

        group = nps[0].get_group()
        next_node = nps[0].get_owner_node()

        group_pads = [
            p
            for p in next_node.pads
            if isinstance(p, pad.StatelessSinkPad) and p.get_group() == group
        ]
        return group_pads
