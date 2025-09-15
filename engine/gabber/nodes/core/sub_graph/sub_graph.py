# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import TYPE_CHECKING, cast

from gabber.core import node, pad
from gabber.core.node import NodeMetadata
from gabber.core.secret import PublicSecret, SecretProvider

from .proxy_property_sink import ProxyPropertySink
from .proxy_property_source import ProxyPropertySource
from .proxy_stateless_sink import ProxyStatelessSink
from .proxy_stateless_source import ProxyStatelessSource

if TYPE_CHECKING:
    from gabber.core.graph import Graph


class SubGraph(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "A reusable subgraph that can be used as a node in other graphs"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="subgraph", secondary="composite", tags=["reusable", "nested"]
        )

    def __init__(
        self,
        *,
        secret_provider: SecretProvider,
        secrets: list[PublicSecret],
        graph: "Graph",
    ):
        super().__init__(secret_provider=secret_provider, secrets=secrets)
        self.graph = graph
        self.loaded = False

    async def run(self):
        await self.graph.run(room=self.room)

    def set_subgraph_id(self, subgraph_id: str):
        subgraph_id_pad = cast(pad.PropertySinkPad, self.get_pad("__subgraph_id__"))
        if not subgraph_id_pad:
            subgraph_id_pad = pad.PropertySinkPad(
                id="__subgraph_id__",
                group="subgraph",
                owner_node=self,
                default_type_constraints=[pad.types.String()],
                value=subgraph_id,
            )
            self.pads.append(subgraph_id_pad)
        subgraph_id_pad.set_value(subgraph_id)

    def resolve_pads(self):
        subgraph_id_pad = cast(pad.PropertySinkPad, self.get_pad("__subgraph_id__"))
        if not subgraph_id_pad:
            subgraph_id_pad = pad.PropertySinkPad(
                id="__subgraph_id__",
                group="subgraph",
                owner_node=self,
                default_type_constraints=[pad.types.String()],
                value="",
            )
            self.pads.append(subgraph_id_pad)

        # Find all existing pads that should be proxies
        swap_to_proxy: list[pad.Pad] = []
        for p in self.pads:
            if p.get_id() == "__subgraph_id__":
                continue

            if not isinstance(p, pad.ProxyPad):
                swap_to_proxy.append(p)

        self.pads = [p for p in self.pads if p not in swap_to_proxy]

        # Find all subgraph pads that need proxying
        subgraph_pad_refs: list[SubgraphPadReference] = []
        for n in self.graph.nodes:
            if (
                not isinstance(n, ProxyStatelessSink)
                and not isinstance(n, ProxyStatelessSource)
                and not isinstance(n, ProxyPropertySink)
                and not isinstance(n, ProxyPropertySource)
            ):
                continue

            p = n.get_pad_required("proxy")

            if isinstance(p, pad.SinkPad):
                prev_pad = p.get_previous_pad()
                if not prev_pad:
                    continue

                prev_group = prev_pad.get_group()
                group_pads = [
                    p
                    for p in prev_pad.get_owner_node().pads
                    if isinstance(p, pad.SourcePad) and p.get_group() == prev_group
                ]
                for idx, gp in enumerate(group_pads):
                    pad_id = n.get_pad_id()
                    if len(group_pads) > 1:
                        pad_id = f"{pad_id}_{idx}"
                    subgraph_pad_refs.append(
                        SubgraphPadReference(
                            subgraph_node=self,
                            pad=gp,
                            new_proxy_id=pad_id,
                            proxy_node_pad=p,
                        )
                    )
            elif isinstance(p, pad.SourcePad):
                next_pads = p.get_next_pads()
                if len(next_pads) == 0:
                    continue
                next_group = next_pads[0].get_group()

                group_pads = [
                    p
                    for p in next_pads[0].get_owner_node().pads
                    if isinstance(p, pad.SinkPad) and p.get_group() == next_group
                ]
                for idx, gp in enumerate(group_pads):
                    pad_id = n.get_pad_id()
                    if len(group_pads) > 1:
                        pad_id = f"{pad_id}_{idx}"
                    subgraph_pad_refs.append(
                        SubgraphPadReference(
                            subgraph_node=self,
                            pad=gp,
                            new_proxy_id=pad_id,
                            proxy_node_pad=p,
                        )
                    )

        # Swap pads that need to be proxies
        sg_pr_to_remove: list[SubgraphPadReference] = []
        while len(swap_to_proxy) > 0:
            p = swap_to_proxy.pop()
            sg_pr: SubgraphPadReference | None = None
            for _sg_pr in subgraph_pad_refs:
                if p.get_id() == _sg_pr.new_proxy_id or p.get_id().startswith(
                    f"{_sg_pr.new_proxy_id}_"
                ):
                    sg_pr = _sg_pr
                    break

            if sg_pr is None:
                logging.error(
                    f"Could not find SubgraphPadReference for pad {p.get_id()}. This should not happen."
                )
                continue

            proxy_p = sg_pr.create_proxy_pad()
            if isinstance(p, pad.SourcePad):
                assert isinstance(proxy_p, pad.SourcePad), (
                    f"Expected SourcePad, got {type(proxy_p)}"
                )
                sg_pr.disconnect_proxy_node_pad()
                next_pads = p.get_next_pads()
                proxy_p.set_next_pads(next_pads)
            elif isinstance(p, pad.SinkPad):
                assert isinstance(proxy_p, pad.SinkPad), (
                    f"Expected SinkPad, got {type(proxy_p)}"
                )
                sg_pr.disconnect_proxy_node_pad()
                previous_pad = p.get_previous_pad()
                p.disconnect()
                if previous_pad:
                    previous_pad.connect(proxy_p)

            if isinstance(p, pad.PropertyPad):
                assert isinstance(proxy_p, pad.PropertyPad), (
                    f"Expected PropertyPad, got {type(proxy_p)}"
                )
                proxy_p.set_value(p.get_value())

            self.pads.append(proxy_p)
            sg_pr_to_remove.append(sg_pr)

        subgraph_pad_refs = [
            sg_pr for sg_pr in subgraph_pad_refs if sg_pr not in sg_pr_to_remove
        ]

        # Create proxy pads for remaining subgraph pad references
        for sg_pr in subgraph_pad_refs:
            proxy_pad = sg_pr.create_proxy_pad()
            self.pads.append(proxy_pad)

            sg_pr.disconnect_proxy_node_pad()

            if isinstance(proxy_pad, pad.PropertyPad):
                assert isinstance(sg_pr.pad, pad.PropertyPad), (
                    f"Expected PropertyPad, got {type(sg_pr.pad)}"
                )
                proxy_pad.set_value(sg_pr.pad.get_value())

        # Sort pads (minus __subgraph_id__)
        self.pads = [subgraph_id_pad] + sorted(
            [p for p in self.pads if p.get_id() != "__subgraph_id__"],
            key=lambda p: (p.get_group(), p.get_id()),
        )


class SubgraphPadReference:
    def __init__(
        self,
        *,
        subgraph_node: node.Node,
        pad: pad.Pad,
        new_proxy_id: str,
        proxy_node_pad: pad.Pad,
    ):
        self.subgraph_node = subgraph_node
        self.pad = pad
        self.new_proxy_id = new_proxy_id
        self.proxy_node_pad = proxy_node_pad

    def create_proxy_pad(self):
        if isinstance(self.pad, pad.StatelessSourcePad):
            return pad.ProxyStatelessSourcePad(
                id=self.new_proxy_id,
                owner_node=self.subgraph_node,
                group=self.pad.get_group(),
                other=self.pad,
            )
        elif isinstance(self.pad, pad.StatelessSinkPad):
            return pad.ProxyStatelessSinkPad(
                id=self.new_proxy_id,
                owner_node=self.subgraph_node,
                group=self.pad.get_group(),
                other=self.pad,
            )
        elif isinstance(self.pad, pad.PropertySourcePad):
            return pad.ProxyPropertySourcePad(
                id=self.new_proxy_id,
                owner_node=self.subgraph_node,
                group=self.pad.get_group(),
                other=self.pad,
            )
        elif isinstance(self.pad, pad.PropertySinkPad):
            return pad.ProxyPropertySinkPad(
                id=self.new_proxy_id,
                owner_node=self.subgraph_node,
                group=self.pad.get_group(),
                other=self.pad,
            )
        else:
            raise ValueError(f"Unsupported pad type: {type(self.pad)}")

    def disconnect_proxy_node_pad(self):
        if isinstance(self.pad, pad.SourcePad):
            assert isinstance(self.proxy_node_pad, pad.SinkPad), (
                f"Expected SinkPad, got {type(self.proxy_node_pad)}"
            )
            self.pad.disconnect(self.proxy_node_pad)
        elif isinstance(self.pad, pad.SinkPad):
            assert isinstance(self.proxy_node_pad, pad.SourcePad), (
                f"Expected SourcePad, got {type(self.proxy_node_pad)}"
            )
            self.proxy_node_pad.disconnect(self.pad)
        else:
            raise ValueError(
                f"Unsupported proxy node pad type: {type(self.proxy_node_pad)}"
            )
