# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, Type, TypeVar, cast

from livekit import rtc

from .. import pad
from ..editor import messages, models, serialize
from ..editor.models import (
    ConnectPadEdit,
    DisconnectPadEdit,
    EditType,
    GraphLibraryItem,
    GraphLibraryItem_Node,
    GraphLibraryItem_SubGraph,
    InsertNodeEdit,
    InsertSubGraphEdit,
    RemoveNodeEdit,
    UpdateNodeEdit,
    UpdatePadEdit,
)
from ..node import Node
from ..secret import PublicSecret, SecretProvider
from gabber.nodes.core.sub_graph import SubGraph
from gabber.utils import short_uuid
from .runtime_api import RuntimeApi
from ..types import pad_constraints, mapper, client

T = TypeVar("T", bound=Node)


class Graph:
    def __init__(
        self,
        *,
        id: str = "default",
        secret_provider: SecretProvider,
        secrets: list[PublicSecret],
        library_items: list[GraphLibraryItem],
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        self.id = id
        self.secret_provider = secret_provider
        self.secrets = secrets
        self.library_items = library_items
        self.logger = logger

        self.nodes: list[Node] = []
        self.portals: list[models.Portal] = []

        self.virtual_nodes: list[tuple[Node, GraphLibraryItem]] = []

        self._node_cls_lookup: dict[str, Type[Node]] = {}
        self._sub_graph_cls_lookup: dict[str, GraphLibraryItem_SubGraph] = {}
        for item in self.library_items:
            if isinstance(item, GraphLibraryItem_Node):
                self._node_cls_lookup[item.name] = item.node_type
                node_cls: Type[Node] = self._node_cls_lookup[item.name]
                n = node_cls(
                    secret_provider=self.secret_provider,
                    secrets=self.secrets,
                    logger=logging.getLogger(f"virtual_node.{item.name}"),
                )
                n.resolve_pads()
                self.virtual_nodes.append((n, item))
            elif isinstance(item, GraphLibraryItem_SubGraph):
                self._sub_graph_cls_lookup[item.id] = item
                # TODO create virtual node

    def get_node(self, node_id: str) -> Node | None:
        return next((n for n in self.nodes if n.id == node_id), None)

    async def handle_request(
        self, request: messages.Request
    ) -> messages.Response | None:
        if request.type == messages.RequestType.LOAD_FROM_SNAPSHOT:
            await self.load_from_snapshot(request.graph)
            return messages.LoadFromSnapshotResponse(
                graph=self.to_editor(), req_id=request.req_id
            )
        elif request.type == messages.RequestType.GET_NODE_LIBRARY:
            return messages.NodeLibraryResponse(
                node_library=self.library_items, req_id=request.req_id
            )
        elif request.type == messages.RequestType.EDIT:
            for e in request.edits:
                try:
                    await self._handle_edit(e)
                except Exception as exc:
                    logging.error(
                        f"Error handling edit in graph: {self.id}-{e}: {exc}",
                        exc_info=exc,
                    )
            return messages.EditResponse(graph=self.to_editor(), req_id=request.req_id)
        elif request.type == messages.RequestType.QUERY_ELIGIBLE_NODE_LIBRARY_ITEMS:
            response = await self._handle_query_eligible_node_library_items(request)
            return response

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
            elif request.type == EditType.CREATE_PORTAL:
                await self._handle_create_portal(request)
            elif request.type == EditType.CREATE_PORTAL_END:
                await self._handle_create_portal_end(request)
            elif request.type == EditType.DELETE_PORTAL:
                await self._handle_delete_portal(request)
            elif request.type == EditType.DELETE_PORTAL_END:
                await self._handle_delete_portal_end(request)
            elif request.type == EditType.UPDATE_PORTAL:
                await self._handle_update_portal(request)
            elif request.type == EditType.UPDATE_PORTAL_END:
                await self._handle_update_portal_end(request)
            else:
                logging.warning(f"Unknown edit type: {request.type}")

        except Exception as e:
            logging.error(
                f"Error handling edit in graph: {self.id}-{request}", exc_info=e
            )

    async def _handle_query_eligible_node_library_items(
        self, req: messages.QueryEligibleNodeLibraryItemsRequest
    ):
        source_node = next((n for n in self.nodes if n.id == req.source_node), None)
        if not source_node:
            raise ValueError(f"Source node with ID {req.source_node} not found.")

        source_pad = source_node.get_pad(req.source_pad)
        if not source_pad:
            raise ValueError(f"Source pad with ID {req.source_pad} not found.")

        if not isinstance(source_pad, pad.SourcePad):
            raise ValueError(f"Source pad with ID {req.source_pad} is not a SourcePad.")

        res: list[models.EligibleLibraryItem] = []

        for vn, li in self.virtual_nodes:
            connectable_pads = [
                p
                for p in vn.pads
                if source_pad.can_connect(p) and isinstance(p, pad.SinkPad)
            ]
            pads: list[models.PadEditorRepresentation] = []
            for p in connectable_pads:
                pads.append(serialize.pad_editor_rep(p))

            if pads:
                res.append(models.EligibleLibraryItem(library_item=li, pads=pads))

        return messages.QueryEligibleNodeLibraryItemsResponse(
            direct_eligible_items=res, autoconvert_eligible_items=[], req_id=req.req_id
        )

    async def _handle_insert_node(self, edit: InsertNodeEdit):
        node_cls: Type[Node] = self._node_cls_lookup[edit.node_type]
        node = node_cls(
            secret_provider=self.secret_provider,
            secrets=self.secrets,
            logger=self.logger,
        )
        if edit.id:
            node.id = edit.id
        else:
            node.id = f"{node_cls.get_type()}_{short_uuid()}".lower()
        node.editor_position = edit.editor_position
        node.editor_name = edit.editor_name
        node.editor_dimensions = edit.editor_dimensions
        node.resolve_pads()
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
            logger=self.logger,
        )
        await graph.load_from_snapshot(subgraph_item.graph)
        node = SubGraph(
            secrets=self.secrets,
            secret_provider=self.secret_provider,
            graph=graph,
            logger=self.logger,
        )
        node.set_subgraph_id(subgraph_item.id)
        if edit.id:
            node.id = edit.id
        else:
            node.id = f"subgraph_{short_uuid()}".lower()
        node.editor_position = edit.editor_position
        node.editor_name = edit.editor_name
        node.editor_dimensions = edit.editor_dimensions
        node.resolve_pads()
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
        self.nodes = new_nodes
        for n in connected_nodes:
            n.resolve_pads()

        self.portals = [p for p in self.portals if p.source_node != node_to_remove]

    async def _handle_connect_pad(self, edit: ConnectPadEdit):
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

        source_pad.connect(target_pad)
        source_node.resolve_pads()
        target_node.resolve_pads()

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

        self.logger.info(
            f"Disconnecting pads: {source_node.id}.{source_pad.get_id()} -> {target_node.id}.{target_pad.get_id()}"
        )
        source_pad.disconnect(target_pad)
        source_node.resolve_pads()
        target_node.resolve_pads()

    async def _handle_update_pad(self, edit: UpdatePadEdit):
        node = next((n for n in self.nodes if n.id == edit.node), None)
        if not node:
            raise ValueError(f"Node with ID {edit.node} not found.")
        p = node.get_pad(edit.pad)
        if not p:
            raise ValueError(f"Pad with ID {edit.pad} not found in node {edit.node}.")

        tcs = p.get_type_constraints()
        if tcs and len(tcs) == 1 and isinstance(p, pad.PropertyPad):
            if isinstance(tcs[0], pad_constraints.NodeReference):
                pass
            else:
                v = mapper.Mapper.client_to_runtime(edit.value)
                p.set_value(v)

        for node in self.nodes:
            node.resolve_pads()

    async def _handle_create_portal(self, edit: models.CreatePortalEdit):
        portal = models.Portal(
            id=f"portal_{short_uuid()}",
            name=f"{edit.source_node}:{edit.source_pad}",
            editor_position=edit.editor_position,
            ends=[],
            source_node=edit.source_node,
            source_pad=edit.source_pad,
        )
        self.portals.append(portal)

    async def _handle_create_portal_end(self, edit: models.CreatePortalEndEdit):
        portal = next((p for p in self.portals if p.id == edit.portal_id), None)
        if not portal:
            raise ValueError(f"Portal with ID {edit.portal_id} not found.")
        portal_end = models.PortalEnd(
            id=f"portal_end_{short_uuid()}",
            editor_position=edit.editor_position,
            next_pads=[],
        )
        portal.ends.append(portal_end)

    async def _handle_delete_portal(self, edit: models.DeletePortalEdit):
        portal = next((p for p in self.portals if p.id == edit.portal_id), None)
        if not portal:
            raise ValueError(f"Portal with ID {edit.portal_id} not found.")
        self.portals = [p for p in self.portals if p.id != edit.portal_id]

    async def _handle_delete_portal_end(self, edit: models.DeletePortalEndEdit):
        portal = next((p for p in self.portals if p.id == edit.portal_id), None)
        if not portal:
            raise ValueError(f"Portal with ID {edit.portal_id} not found.")
        portal_end = next((e for e in portal.ends if e.id == edit.portal_end_id), None)
        if not portal_end:
            raise ValueError(f"Portal end with ID {edit.portal_end_id} not found.")

        portal.ends = [e for e in portal.ends if e.id != edit.portal_end_id]
        nps = portal_end.next_pads
        source_node = next((n for n in self.nodes if n.id == portal.source_node), None)
        if not source_node:
            logging.warning(
                f"Source node with ID {portal.source_node} not found when deleting portal end."
            )
            return

        for np in nps:
            target_node = next((n for n in self.nodes if n.id == np.node), None)
            if not target_node:
                logging.warning(
                    f"Target node with ID {np.node} not found when deleting portal end."
                )
                continue
            target_pad = cast(pad.SinkPad, target_node.get_pad(np.pad))
            if not target_pad:
                logging.warning(
                    f"Target pad with ID {np.pad} not found in node {np.node} when deleting portal end."
                )
                continue

            target_pad.disconnect()

            target_node.resolve_pads()

        source_node.resolve_pads()

    async def _handle_update_portal(self, edit: models.UpdatePortalEdit):
        portal = next((p for p in self.portals if p.id == edit.portal_id), None)
        if not portal:
            raise ValueError(f"Portal with ID {edit.portal_id} not found.")
        portal.editor_position = edit.editor_position

    async def _handle_update_portal_end(self, edit: models.UpdatePortalEndEdit):
        portal = next((p for p in self.portals if p.id == edit.portal_id), None)
        if not portal:
            raise ValueError(f"Portal with ID {edit.portal_id} not found.")
        portal_end = next((e for e in portal.ends if e.id == edit.portal_end_id), None)
        if not portal_end:
            raise ValueError(f"Portal end with ID {edit.portal_end_id} not found.")
        portal_end.editor_position = edit.editor_position
        portal_end.next_pads = edit.next_pads

    def to_editor(self):
        nodes: list[models.NodeEditorRepresentation] = []
        for node in self.nodes:
            try:
                editor_rep = serialize.node_editor_rep(node)
                nodes.append(editor_rep)
            except Exception as e:
                logging.error(f"Error serializing node {node.id}: {e}", exc_info=e)
                continue
        return models.GraphEditorRepresentation(nodes=nodes, portals=self.portals)

    async def load_from_snapshot(self, snapshot: messages.GraphEditorRepresentation):
        self.nodes = []

        for node_data in snapshot.nodes:
            node: Node
            node_cls: Type[Node] | None = self._node_cls_lookup.get(node_data.type)
            if node_cls:
                node_logger = logging.LoggerAdapter(
                    self.logger, extra={"node": node_data.id}
                )
                node = node_cls(
                    secret_provider=self.secret_provider,
                    secrets=self.secrets,
                    logger=node_logger,
                )
            elif node_data.type == "SubGraph":
                subgraph_id_pad = next(
                    (p for p in node_data.pads if p.id == "__subgraph_id__"), None
                )
                if not subgraph_id_pad:
                    logging.error("SubGraph node must have a '__subgraph_id__' pad. ")
                    continue

                subgraph_id = subgraph_id_pad.value
                assert (
                    isinstance(subgraph_id, client.ClientPadValue)
                    and subgraph_id is not None
                    and subgraph_id.type == "string"
                )
                subgraph_li: GraphLibraryItem_SubGraph | None = None
                for item in self.library_items:
                    if item.type == "subgraph" and subgraph_id.value == item.id:
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
                    logger=self.logger,
                )
                await subgraph.load_from_snapshot(subgraph_li.graph)
                node = SubGraph(
                    secret_provider=self.secret_provider,
                    secrets=self.secrets,
                    graph=subgraph,
                    logger=self.logger,
                )
            else:
                logging.error(f"Node type {node_data.type} not found in library.")
                continue

            node.id = node_data.id
            node.editor_position = node_data.editor_position
            node.editor_name = node_data.editor_name
            node.editor_dimensions = node_data.editor_dimensions
            for p in node_data.pads:
                p_obj = create_pad_from_editor(p, owner_node=node)
                node.pads.append(p_obj)

            self.nodes.append(node)

        node_lookup: dict[str, Node] = {n.id: n for n in self.nodes}
        # Handle pad links
        for n in snapshot.nodes:
            node_obj = node_lookup.get(n.id)
            if not node_obj:
                logging.error(f"Node {n.id} not found in node lookup.")
                continue
            for p in n.pads:
                for link_id in p.pad_links:
                    source_pad = node_obj.get_pad(p.id)
                    link_pad = node_obj.get_pad(link_id)
                    if not source_pad or not link_pad:
                        logging.error(
                            f"Pad {p.id} or linked pad {link_id} not found in node {n.id}."
                        )
                        continue
                    source_pad.link_types_to_pad(link_pad)

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

            node_obj = node_lookup.get(node_data.id)
            if not node_obj:
                logging.error(f"Node {node_data.id} not found in node lookup.")
                continue

        # resolve node references
        for n in self.nodes:
            for p in n.pads:
                tcs = p.get_type_constraints()
                if tcs and len(tcs) == 1:
                    if isinstance(tcs[0], pad_constraints.NodeReference) and isinstance(
                        p, pad.PropertyPad
                    ):
                        self._resolve_node_reference_property(
                            p, p.get_value(), node_lookup
                        )

        for n in self.nodes:
            n.resolve_pads()

        # resolve secret options
        secret_options = await self.secret_provider.list_secrets()
        for n in self.nodes:
            for p in n.pads:
                tcs = p.get_type_constraints()
                d_tcs = p.get_default_type_constraints()
                if tcs and len(tcs) == 1:
                    if isinstance(tcs[0], pad_constraints.Secret):
                        tcs[0].options = secret_options
                        if isinstance(p, pad.PropertyPad) and p.get_value() not in [
                            s.id for s in secret_options
                        ]:
                            p.set_value(None)
                if d_tcs and len(d_tcs) == 1:
                    if isinstance(d_tcs[0], pad_constraints.Secret):
                        d_tcs[0].options = secret_options

        if snapshot.portals:
            self.portals = snapshot.portals

    def _resolve_node_reference_property(
        self, p: pad.PropertyPad, v: str, nodes: dict[str, Node]
    ):
        if not isinstance(p, pad.SourcePad):
            return

        # Proxy pads would already be handled by the subgraph
        if not isinstance(p, pad.ProxyPad):
            node = next((n for n in nodes.values() if n.id == v), None)
            p.set_value(node)
            return

    async def run(self, room: rtc.Room, runtime_api: RuntimeApi | None = None):
        for node in self.nodes:
            node.room = room

        runtime_api_t = asyncio.create_task(
            runtime_api.run(nodes=self.nodes) if runtime_api else asyncio.sleep(0)
        )
        node_tasks: list[asyncio.Task] = []
        try:

            async def node_run_wrapper(n: Node):
                try:
                    await n.run()
                    n.logger.info(f"Node {n.id} run completed.")
                except Exception as e:
                    n.logger.error(f"Error in node {n.id} run: {e}", exc_info=e)

            node_tasks = [
                asyncio.create_task(node_run_wrapper(n), name=f"node_{n.id}")
                for n in self.nodes
            ]
            await asyncio.gather(
                *node_tasks,
                runtime_api_t,
            )
        except asyncio.CancelledError:
            self.logger.info("Graph run cancelled, shutting down nodes.")
            runtime_api_t.cancel()
            for n_t in node_tasks:
                n_t.cancel()
        except Exception as e:
            logging.error(f"Error running graph: {e}", exc_info=e)

        try:
            await runtime_api_t
        except asyncio.CancelledError:
            self.logger.info("Runtime API run cancelled.")

        for n_t in node_tasks:
            try:
                await n_t
            except asyncio.CancelledError:
                self.logger.info(f"Node {n_t.get_name()} run cancelled.")

        self.logger.info("Graph run completed.")


def create_pad_from_editor(
    e: models.PadEditorRepresentation, owner_node: Node
) -> pad.Pad:
    p: pad.Pad
    default_allowed_types = cast(
        list[pad_constraints.BasePadType] | None, e.default_allowed_types
    )
    allowed_types = cast(list[pad_constraints.BasePadType] | None, e.allowed_types)
    if e.type == "PropertySourcePad":
        logging.debug(f"Creating PropertySourcePad {e.id} with value {e.value}")
        v: Any = None
        if allowed_types and len(allowed_types) == 1:
            v = mapper.Mapper.client_to_runtime(e.value)
        p = pad.PropertySourcePad(
            id=e.id,
            group=e.group,
            owner_node=owner_node,
            default_type_constraints=default_allowed_types,
            value=v,
        )
    elif e.type == "PropertySinkPad":
        v: Any = None
        if allowed_types and len(allowed_types) == 1:
            v = mapper.Mapper.client_to_runtime(e.value)
        p = pad.PropertySinkPad(
            id=e.id,
            group=e.group,
            owner_node=owner_node,
            default_type_constraints=default_allowed_types,
            value=v,
        )
    elif e.type == "StatelessSourcePad":
        p = pad.StatelessSourcePad(
            id=e.id,
            group=e.group,
            owner_node=owner_node,
            default_type_constraints=default_allowed_types,
        )
    elif e.type == "StatelessSinkPad":
        p = pad.StatelessSinkPad(
            id=e.id,
            group=e.group,
            owner_node=owner_node,
            default_type_constraints=default_allowed_types,
        )
    else:
        raise ValueError(f"Unknown pad type: {e.type}")

    p.set_type_constraints(allowed_types)
    return p
