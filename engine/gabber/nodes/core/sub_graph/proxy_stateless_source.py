# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from gabber.core import node, pad
from gabber.core.node import NodeMetadata
from utils import short_uuid


class ProxyStatelessSource(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Proxy source pad for subgraph connections"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="subgraph", secondary="source", tags=["stateless", "proxy"]
        )

    def resolve_pads(self):
        proxy_pad = cast(pad.StatelessSinkPad, self.get_pad("proxy"))
        if not proxy_pad:
            self.pads.append(
                pad.StatelessSinkPad(
                    id="proxy",
                    owner_node=self,
                    group="proxy",
                    default_type_constraints=None,
                )
            )
            proxy_pad = cast(pad.StatelessSinkPad, self.get_pad("proxy"))

        pad_id = cast(pad.PropertySinkPad, self.get_pad("pad_id"))
        if not pad_id:
            self.pads.append(
                pad.PropertySinkPad(
                    id="pad_id",
                    owner_node=self,
                    group="pad_id",
                    default_type_constraints=[pad.types.String()],
                    value=f"proxy_{short_uuid()}",
                )
            )
            pad_id = cast(pad.PropertySinkPad, self.get_pad("pad_id"))

        tsc = None
        prev_pad = proxy_pad.get_previous_pad()
        if prev_pad:
            prev_pad = cast(pad.PropertySourcePad, prev_pad)
            tsc = pad.types.INTERSECTION(tsc, prev_pad.get_type_constraints())
        proxy_pad.set_type_constraints(tsc)

    def get_pad_id(self) -> str:
        pad_id = cast(pad.PropertySinkPad, self.get_pad_required("pad_id"))
        return pad_id.get_value()

    def get_proxy_target_pads(self) -> list[pad.StatelessSourcePad]:
        proxy_pad = cast(pad.StatelessSinkPad, self.get_pad_required("proxy"))
        pp = proxy_pad.get_previous_pad()
        if not pp:
            return []

        first = cast(pad.StatelessSourcePad, pp)
        group = first.get_group()
        return [
            p
            for p in first.get_owner_node().pads
            if p.get_group() == group and isinstance(p, pad.StatelessSourcePad)
        ]
