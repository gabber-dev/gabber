# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, Type, TypeVar, cast

from livekit import rtc
from nodes.core.sub_graph import SubGraph
from utils import short_uuid

from core import pad, runtime_types
from core.editor import messages, models, serialize
from core.editor.models import (
    ConnectPadEdit,
    DisconnectPadEdit,
    EditType,
    GraphLibraryItem,
    GraphLibraryItem_Node,
    GraphLibraryItem_SubGraph,
    InsertNodeEdit,
    InsertSubGraphEdit,
    RemoveNodeEdit,
    ToggleDisplayStateEdit,
    UpdateNodeEdit,
    UpdatePadEdit,
)
from core.node import Node
from core.secret import PublicSecret, SecretProvider

T = TypeVar("T", bound=Node)


class Graph:
    def __init__(
        self,
        *,
        id: str = "default",
        secret_provider: SecretProvider,
        secrets: list[PublicSecret],
        library_items: list[GraphLibraryItem],
    ):
        self.id = id
        self.secret_provider = secret_provider
        self.secrets = secrets
        self.library_items = library_items

        self.nodes: list[Node] = []

        self._node_cls_lookup: dict[str, Type[Node]] = {}
        self._sub_graph_cls_lookup: dict[str, GraphLibraryItem_SubGraph] = {}
        for item in self.library_items:
            if isinstance(item, GraphLibraryItem_Node):
                self._node_cls_lookup[item.name] = item.node_type
            elif isinstance(item, GraphLibraryItem_SubGraph):
                self._sub_graph_cls_lookup[item.id] = item

    def get_node(self, node_id: str) -> Node | None:
        return next((n for n in self.nodes if n.id == node_id), None)

    async def handle_request(
        self, request: messages.Request
    ) -> messages.Response | None:
        if request.type == messages.RequestType.LOAD_FROM_SNAPSHOT:
            await self.load_from_snapshot(request.graph)
            return messages.Response(
                response=messages.FullGraphResponse(graph=self.to_editor())
            )
        elif request.type == messages.RequestType.GET_NODE_LIBRARY:
            return messages.Response(
                response=messages.NodeLibraryResponse(node_library=self.library_items)
            )
        elif request.type == messages.RequestType.EDIT:
            await self._handle_edit(request.edit)
            return messages.Response(
                response=messages.FullGraphResponse(graph=self.to_editor())
            )

    async def _handle_edit(self, request: messages.Edit):
        try:
            if request.type == EditType.INSERT_NODE:
                await self._handle_insert_node(request)
            elif request.type == EditType.INSERT_SUBGRAPH:
                await self._handle_insert_subgraph(request)
            elif request.type == EditType.UPDATE_NODE:
                await self._handle_update_node(request)
            elif request.type == EditType.REMOVE_NODE:
                await self._handle_remove_node(request)
            elif request.type == EditType.CONNECT_PAD:
                await self._handle_connect_pad(request)
            elif request.type == EditType.DISCONNECT_PAD:
                await self._handle_disconnect_pad(request)
            elif request.type == EditType.UPDATE_PAD:
                await self._handle_update_pad(request)
            elif request.type == EditType.TOGGLE_DISPLAY_STATE:
                await self._handle_toggle_display_state(request)

            return True
        except Exception as e:
            logging.error(
                f"Error handling edit in graph: {self.id}-{request}: {e}", exc_info=e
            )
            return False

    async def _handle_insert_node(self, edit: InsertNodeEdit):
        node_cls = self._node_cls_lookup[edit.node_type]
        node = node_cls(secret_provider=self.secret_provider, secrets=self.secrets)
        if edit.id:
            node.id = edit.id
        else:
            node.id = f"{node_cls.get_type()}_{short_uuid()}".lower()
        node.editor_position = edit.editor_position
        node.editor_name = edit.editor_name
        node.editor_dimensions = edit.editor_dimensions
        await self._propagate_update([node])
        self.nodes.append(node)

    async def _handle_insert_subgraph(self, edit: InsertSubGraphEdit):
        subgraph_item = self._sub_graph_cls_lookup.get(edit.subgraph_id)
        if not subgraph_item:
            raise ValueError(f"Subgraph with ID {edit.subgraph_id} not found.")

        graph = Graph(
            id=subgraph_item.id,
            secret_provider=self.secret_provider,
            secrets=self.secrets,
            library_items=self.library_items,
        )
        await graph.load_from_snapshot(subgraph_item.graph)
        node = SubGraph(
            secrets=self.secrets,
            secret_provider=self.secret_provider,
            graph=graph,
        )
        node.set_subgraph_id(subgraph_item.id)
        if edit.id:
            node.id = edit.id
        else:
            node.id = f"subgraph_{short_uuid()}".lower()
        node.editor_position = edit.editor_position
        node.editor_name = edit.editor_name
        node.editor_dimensions = edit.editor_dimensions
        await self._propagate_update([node])
        self.nodes.append(node)

    async def _handle_update_node(self, edit: UpdateNodeEdit):
        node: Node | None = next((n for n in self.nodes if n.id == edit.id), None)
        if not node:
            raise ValueError(f"Node with ID {edit.id} not found.")

        if edit.editor_position:
            node.editor_position = edit.editor_position
        if edit.editor_name:
            node.editor_name = edit.editor_name
        if edit.editor_dimensions:
            node.editor_dimensions = edit.editor_dimensions
        if edit.new_id and edit.new_id != edit.id:
            old_id = edit.id
            new_id = edit.new_id

            # Check if new ID already exists
            if any(n.id == new_id for n in self.nodes if n.id != old_id):
                raise ValueError(f"Node with ID {new_id} already exists.")

            node.id = new_id

    async def _handle_remove_node(self, edit: RemoveNodeEdit):
        node_to_remove = next((n for n in self.nodes if n.id == edit.node_id), None)
        if not node_to_remove:
            raise ValueError(f"Node with ID {edit.node_id} not found.")
        new_nodes = [n for n in self.nodes if n.id != edit.node_id]
        connected_nodes = node_to_remove.get_connected_nodes()
        node_to_remove.disconnect_all()
        await self._propagate_update(connected_nodes)
        self.nodes = new_nodes

    async def _handle_connect_pad(self, edit: ConnectPadEdit):
        source_node = next((n for n in self.nodes if n.id == edit.node), None)
        target_node = next((n for n in self.nodes if n.id == edit.connected_node), None)
        if not source_node or not target_node:
            raise ValueError("Source or target node not found.")

        # Resolve consolidated pad connections
        source_pad_id = self._resolve_pad_id(source_node, edit.pad)
        target_pad_id = self._resolve_pad_id(target_node, edit.connected_pad)

        source_pad = source_node.get_pad(source_pad_id)
        target_pad = target_node.get_pad(target_pad_id)

        if not source_pad or not target_pad:
            raise ValueError("Source or target pad not found.")

        if not isinstance(source_pad, pad.SourcePad):
            raise ValueError("Source pad is not a source pad type.")

        source_pad.connect(cast(Any, target_pad))

        await self._propagate_update([source_node, target_node])

    def _resolve_pad_id(self, node: Node, pad_id: str) -> str:
        """Resolve consolidated pad IDs to actual pad IDs"""
        if pad_id == f"{node.id}-consolidated-sink":
            # For consolidated sink, connect to the first available sink pad
            for p in node.pads:
                if isinstance(p, pad.SinkPad):
                    return p.get_id()
        elif pad_id == f"{node.id}-consolidated-source":
            # For consolidated source, connect to the first available source pad
            for p in node.pads:
                if isinstance(p, pad.SourcePad):
                    return p.get_id()
        
        # Return original pad_id if not a consolidated pad
        return pad_id

    async def _handle_disconnect_pad(self, edit: DisconnectPadEdit):
        source_node = next((n for n in self.nodes if n.id == edit.node), None)
        target_node = next((n for n in self.nodes if n.id == edit.connected_node), None)

        if not source_node or not target_node:
            raise ValueError("Source or target node not found.")

        source_pad = source_node.get_pad(edit.pad)
        target_pad = target_node.get_pad(edit.connected_pad)

        if not source_pad or not target_pad:
            raise ValueError("Source or target pad not found.")

        if not isinstance(source_pad, pad.SourcePad):
            raise ValueError("Source pad is not a source pad type.")

        if not isinstance(target_pad, pad.SinkPad):
            raise ValueError("Target pad is not a sink pad type.")

        source_pad.disconnect(target_pad)
        await self._propagate_update([source_node, target_node])

    async def _handle_update_pad(self, edit: UpdatePadEdit):
        node = next((n for n in self.nodes if n.id == edit.node), None)
        if not node:
            raise ValueError(f"Node with ID {edit.node} not found.")
        p = node.get_pad(edit.pad)
        if not p:
            raise ValueError(f"Pad with ID {edit.pad} not found in node {edit.node}.")

        v = serialize.deserialize_pad_value(self.nodes, p, edit.value)
        if isinstance(p, pad.PropertyPad):
            p.set_value(v)

        await self._propagate_update([node])

    async def _handle_toggle_display_state(self, edit: ToggleDisplayStateEdit):
        node = next((n for n in self.nodes if n.id == edit.node_id), None)
        if not node:
            raise ValueError(f"Node with ID {edit.node_id} not found.")
        
        node.toggle_display_state()
        
        # No need to propagate update as this is just a visual change
        # The serialization will pick up the new display state

    async def _propagate_update(self, starting_nodes: list[Node]):
        seen: set[str] = set()
        stack: list[Node] = starting_nodes[:]
        while stack:
            node = stack.pop()
            if node.id in seen:
                continue
            seen.add(node.id)
            await node.resolve_pads()
            connected_nodes = node.get_connected_nodes()
            stack.extend(connected_nodes)

    def to_editor(self):
        nodes = [serialize.node_editor_rep(n) for n in self.nodes]
        return models.GraphEditorRepresentation(nodes=nodes)

    async def load_from_snapshot(self, snapshot: messages.GraphEditorRepresentation):
        self.nodes = []
        for node_data in snapshot.nodes:
            node: Node
            node_cls = self._node_cls_lookup.get(node_data.type)
            if node_cls:
                node = node_cls(
                    secret_provider=self.secret_provider,
                    secrets=self.secrets,
                )
            elif node_data.type == "SubGraph":
                subgraph_id_pad = next(
                    (p for p in node_data.pads if p.id == "__subgraph_id__"), None
                )
                if not subgraph_id_pad:
                    logging.error("SubGraph node must have a '__subgraph_id__' pad. ")
                    continue

                subgraph_id = subgraph_id_pad.value
                subgraph_li: GraphLibraryItem_SubGraph | None = None
                for item in self.library_items:
                    if (
                        isinstance(item, GraphLibraryItem_SubGraph)
                        and item.id == subgraph_id
                    ):
                        subgraph_li = item
                        break

                if not subgraph_li:
                    logging.error(
                        f"SubGraph with ID {subgraph_id} not found in library items."
                    )
                    continue

                subgraph = Graph(
                    id=subgraph_li.id,
                    secret_provider=self.secret_provider,
                    secrets=self.secrets,
                    library_items=self.library_items,
                )
                await subgraph.load_from_snapshot(subgraph_li.graph)
                node = SubGraph(
                    secret_provider=self.secret_provider,
                    secrets=self.secrets,
                    graph=subgraph,
                )
            else:
                raise ValueError(f"Node type {node_data.type} not found in library.")

            node.id = node_data.id
            node.editor_position = node_data.editor_position
            node.editor_name = node_data.editor_name
            node.editor_dimensions = node_data.editor_dimensions
            node.display_state = node_data.display_state.value

            for pad_data in node_data.pads:
                casted_allowed_types = cast(
                    list[pad.types.BasePadType] | None, pad_data.allowed_types
                )
                if pad_data.type == "PropertySinkPad":
                    pad_instance = pad.PropertySinkPad(
                        id=pad_data.id,
                        owner_node=node,
                        group=pad_data.group,
                        type_constraints=casted_allowed_types,
                        value=pad_data.value,
                    )
                    node.pads.append(pad_instance)
                elif pad_data.type == "PropertySourcePad":
                    pad_instance = pad.PropertySourcePad(
                        id=pad_data.id,
                        owner_node=node,
                        group=pad_data.group,
                        type_constraints=casted_allowed_types,
                        value=pad_data.value,
                    )
                    node.pads.append(pad_instance)
                elif pad_data.type == "StatelessSinkPad":
                    pad_instance = pad.StatelessSinkPad(
                        id=pad_data.id,
                        owner_node=node,
                        group=pad_data.group,
                        type_constraints=casted_allowed_types,
                    )
                    node.pads.append(pad_instance)
                elif pad_data.type == "StatelessSourcePad":
                    pad_instance = pad.StatelessSourcePad(
                        id=pad_data.id,
                        owner_node=node,
                        group=pad_data.group,
                        type_constraints=casted_allowed_types,
                    )
                    node.pads.append(pad_instance)
            self.nodes.append(node)

        node_lookup: dict[str, Node] = {n.id: n for n in self.nodes}
        for node_data in snapshot.nodes:
            for pad_data in node_data.pads:
                prev_pad = pad_data.previous_pad
                if not prev_pad:
                    continue

                source_node = node_lookup.get(prev_pad.node)
                target_node = node_lookup.get(node_data.id)
                if not source_node or not target_node:
                    logging.error(
                        f"Node not found for pad connection: {prev_pad.node} or {node_data.id}"
                    )
                    continue
                target_pad = target_node.get_pad(pad_data.id)
                source_pad = source_node.get_pad(prev_pad.pad)

                if not target_pad or not source_pad:
                    logging.error(
                        f"Pad not found for connection: {prev_pad.pad} in {source_node.id} or {pad_data.id} in {target_node.id}"
                    )
                    continue

                if not isinstance(source_pad, pad.SourcePad):
                    logging.error(
                        f"Source pad {prev_pad.pad} in node {prev_pad.node} is not a SourcePad."
                    )
                    continue

                if not isinstance(target_pad, pad.SinkPad):
                    logging.error(
                        f"Target pad {pad_data.id} in node {node_data.id} is not a SinkPad."
                    )
                    continue
                source_pad.connect(target_pad)
                await self._propagate_update([source_node, target_node])

    async def run(self, room: rtc.Room):
        def on_data(packet: rtc.DataPacket):
            if not packet.topic:
                return
            split = packet.topic.split(":")
            node_id = split[0] if len(split) > 0 else None
            pad_id = split[1] if len(split) > 1 else None
            if not node_id or not pad_id:
                logging.error(f"Invalid topic format: {packet.topic}")
                return
            data_type = split[2] if len(split) > 2 else None
            if data_type == "trigger":
                node = next((n for n in self.nodes if n.id == node_id), None)
                if not node:
                    logging.error(f"Node with ID {node_id} not found.")
                    return

                p = node.get_pad(pad_id)
                if not p:
                    logging.error(f"Pad with ID {pad_id} not found in node {node_id}.")
                    return

                if not isinstance(p, pad.SourcePad):
                    logging.error(f"Pad {pad_id} in node {node_id} is not a SourcePad.")
                    return

                ctx = pad.RequestContext(parent=None)
                p.push_item(runtime_types.Trigger(), ctx)
                ctx.complete()

        # Only top level graph gets events
        if self.id == "default":
            room.on("data_received", on_data)

        for node in self.nodes:
            node.room = room

        try:
            await asyncio.gather(*[node.run() for node in self.nodes])
        except Exception as e:
            logging.error(f"Error running graph: {e}", exc_info=e)

        if self.id == "default":
            room.off("data_received", on_data)
