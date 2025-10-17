# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field
from ..types import pad_constraints, client


class NodeMetadata(BaseModel):
    primary: str
    secondary: str
    tags: list[str] = []


class NodeNoteRecommendation(BaseModel):
    message: str
    edits: list["Edit"] | None = None


class NodeNote(BaseModel):
    level: Literal["info", "warning", "error"]
    message: str
    pad: str | None = None
    recommendations: list[NodeNoteRecommendation] | None = None


class EditType(str, Enum):
    INSERT_NODE = "insert_node"
    INSERT_SUBGRAPH = "insert_sub_graph"
    UPDATE_NODE = "update_node"
    REMOVE_NODE = "remove_node"
    CONNECT_PAD = "connect_pad"
    DISCONNECT_PAD = "disconnect_pad"
    UPDATE_PAD = "update_pad"
    CREATE_PORTAL = "create_portal"
    CREATE_PORTAL_END = "create_portal_end"
    DELETE_PORTAL = "delete_portal"
    DELETE_PORTAL_END = "delete_portal_end"
    UPDATE_PORTAL = "update_portal"
    UPDATE_PORTAL_END = "update_portal_end"


class InsertNodeEdit(BaseModel):
    type: Literal[EditType.INSERT_NODE] = EditType.INSERT_NODE
    id: str | None = None
    node_type: str
    editor_position: tuple[float, float]
    editor_dimensions: tuple[float, float] | None = None
    editor_name: str


class InsertSubGraphEdit(BaseModel):
    type: Literal[EditType.INSERT_SUBGRAPH] = EditType.INSERT_SUBGRAPH
    id: str | None = None
    subgraph_id: str
    editor_position: tuple[float, float]
    editor_dimensions: tuple[float, float] | None = None
    editor_name: str


class RemoveNodeEdit(BaseModel):
    type: Literal[EditType.REMOVE_NODE] = EditType.REMOVE_NODE
    node_id: str = Field(..., description="ID of the node to remove")


class UpdateNodeEdit(BaseModel):
    type: Literal[EditType.UPDATE_NODE] = EditType.UPDATE_NODE
    id: str
    editor_position: tuple[float, float] | None
    editor_dimensions: tuple[float, float] | None
    editor_name: str | None
    new_id: str | None = None


class ConnectPadEdit(BaseModel):
    type: Literal[EditType.CONNECT_PAD] = EditType.CONNECT_PAD
    node: str = Field(..., description="ID of the source node")
    pad: str = Field(..., description="Handle ID of the source pad")
    connected_node: str = Field(..., description="ID of the target node")
    connected_pad: str = Field(..., description="Handle ID of the target pad")


class DisconnectPadEdit(BaseModel):
    type: Literal[EditType.DISCONNECT_PAD] = EditType.DISCONNECT_PAD
    node: str = Field(..., description="ID of the source node")
    pad: str = Field(..., description="Handle ID of the source pad")
    connected_node: str = Field(..., description="ID of the target node")
    connected_pad: str = Field(..., description="Handle ID of the target pad")


class UpdatePadEdit(BaseModel):
    type: Literal[EditType.UPDATE_PAD] = EditType.UPDATE_PAD
    node: str = Field(..., description="ID of the node containing the pad")
    pad: str = Field(..., description="ID of the pad to update")
    value: client.ClientPadValue = Field(..., description="New value for the pad")


class CreatePortalEdit(BaseModel):
    type: Literal[EditType.CREATE_PORTAL] = EditType.CREATE_PORTAL
    source_node: str
    source_pad: str
    editor_position: tuple[float, float]


class CreatePortalEndEdit(BaseModel):
    type: Literal[EditType.CREATE_PORTAL_END] = EditType.CREATE_PORTAL_END
    portal_id: str
    editor_position: tuple[float, float]


class UpdatePortalEdit(BaseModel):
    type: Literal[EditType.UPDATE_PORTAL] = EditType.UPDATE_PORTAL
    portal_id: str
    editor_position: tuple[float, float]


class UpdatePortalEndEdit(BaseModel):
    type: Literal[EditType.UPDATE_PORTAL_END] = EditType.UPDATE_PORTAL_END
    portal_id: str
    portal_end_id: str
    editor_position: tuple[float, float]
    next_pads: list["PadReference"]


class DeletePortalEdit(BaseModel):
    type: Literal[EditType.DELETE_PORTAL] = EditType.DELETE_PORTAL
    portal_id: str


class DeletePortalEndEdit(BaseModel):
    type: Literal[EditType.DELETE_PORTAL_END] = EditType.DELETE_PORTAL_END
    portal_id: str
    portal_end_id: str


Edit = Annotated[
    InsertNodeEdit
    | InsertSubGraphEdit
    | UpdateNodeEdit
    | RemoveNodeEdit
    | ConnectPadEdit
    | DisconnectPadEdit
    | UpdatePadEdit
    | CreatePortalEdit
    | CreatePortalEndEdit
    | DeletePortalEdit
    | DeletePortalEndEdit
    | UpdatePortalEdit
    | UpdatePortalEndEdit,
    Field(
        discriminator="type", description="Type of edit to perform on the graph editor"
    ),
]


class GraphEditorRepresentation(BaseModel):
    nodes: list["NodeEditorRepresentation"]
    portals: list["Portal"] | None = []


class GraphLibraryItem_Node(BaseModel):
    type: Literal["node"] = "node"
    name: str = Field(..., description="Name of the node")
    node_type: Any = Field(..., description="Class of the node", exclude=True)
    description: str = Field(
        ..., description="Human-readable description of what the node does"
    )
    metadata: NodeMetadata = Field(
        ..., description="Metadata for categorizing and filtering nodes"
    )


class GraphLibraryItem_SubGraph(BaseModel):
    type: Literal["subgraph"] = "subgraph"
    id: str = Field(..., description="ID of the subgraph")
    name: str = Field(..., description="Name of the subgraph")
    graph: GraphEditorRepresentation = Field(
        ..., description="Graph representation of the subgraph"
    )
    editable: bool = Field(
        True, description="Whether the subgraph can be edited in the editor"
    )


GraphLibraryItem = Annotated[
    GraphLibraryItem_Node | GraphLibraryItem_SubGraph,
    Field(discriminator="type", description="Type of graph library item"),
]


class SubGraph(BaseModel):
    id: str
    graph: GraphEditorRepresentation


class PadReference(BaseModel):
    node: str
    pad: str


class PadEditorRepresentation(BaseModel):
    id: str
    group: str
    type: str
    default_allowed_types: list[pad_constraints.PadConstraint] | None = None
    allowed_types: list[pad_constraints.PadConstraint] | None = None
    value: client.DiscriminatedClientPadValue | Any | None = None
    next_pads: list[PadReference]
    previous_pad: PadReference | None = None
    pad_links: list[str] = []

    class Config:
        # Enable arbitrary types to allow Any
        arbitrary_types_allowed = True


class NodeEditorRepresentation(BaseModel):
    id: str
    type: str
    editor_name: str
    editor_position: tuple[float, float]
    editor_dimensions: tuple[float, float] | None = None
    pads: list[PadEditorRepresentation]
    description: str | None = None
    metadata: NodeMetadata
    notes: list[NodeNote] | None = None


class PortalEnd(BaseModel):
    id: str
    editor_position: tuple[float, float]
    next_pads: list[PadReference]


class Portal(BaseModel):
    id: str
    name: str
    source_node: str
    source_pad: str
    editor_position: tuple[float, float]
    ends: list[PortalEnd] = []


class EligibleLibraryItem(BaseModel):
    library_item: GraphLibraryItem
    pads: list[PadEditorRepresentation]
