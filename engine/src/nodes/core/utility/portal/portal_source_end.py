# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from core import pad, runtime_types
from core.node import Node, NodeMetadata
from .portal_source_start import PortalSourceStart


class PortalSourceEnd(Node):
    def resolve_pads(self):
        source = cast(pad.SourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                group="source",
                owner_node=self,
                default_type_constraints=None,
            )

        start_ref = cast(pad.PropertySinkPad, self.get_pad("start_ref"))
        if not start_ref:
            start_ref = pad.PropertySinkPad(
                id="start_ref",
                group="start_ref",
                owner_node=self,
                default_type_constraints=[
                    pad.types.NodeReference(node_types=["PortalSourceStart"])
                ],
            )

        start_node = start_ref.get_value()
        logging.info(
            "NEIL source pad %s - %s - %s",
            source,
            start_node,
            cast(pad.PropertyPad, start_ref.get_previous_pad()).get_value(),
        )
        if start_node:
            start_node = cast(PortalSourceStart, start_node)
            start_pad = cast(
                pad.SinkPad, start_node.get_pad_required("sink")
            ).get_previous_pad()
            is_property = isinstance(start_pad, pad.PropertyPad)
            needs_proxy = False
            if not isinstance(source, pad.ProxyPad):
                needs_proxy = True
            else:
                if is_property and not isinstance(source, pad.PropertyPad):
                    needs_proxy = True
                elif not is_property and not isinstance(source, pad.StatelessSourcePad):
                    needs_proxy = True

            if needs_proxy:
                if is_property:
                    source = pad.ProxyPropertySourcePad(
                        id="source",
                        group="source",
                        owner_node=self,
                        other=start_pad,
                    )
                else:
                    source = pad.ProxyStatelessSourcePad(
                        id="source",
                        group="source",
                        owner_node=self,
                        other=start_pad,
                    )
        else:
            if not isinstance(source, pad.StatelessSourcePad):
                source.disconnect_all()
                source = pad.StatelessSourcePad(
                    id="source",
                    group="source",
                    owner_node=self,
                    default_type_constraints=None,
                )

        self.pads = [source, start_ref]

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
