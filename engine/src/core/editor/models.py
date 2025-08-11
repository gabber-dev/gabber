# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from enum import Enum
from typing import Annotated, Any, Generic, Literal, Type, TypeVar

from pydantic import BaseModel, Field

from core.node import Node, NodeMetadata
from core.pad import types


class EditType(str, Enum):
    INSERT_NODE = "insert_node"
    INSERT_SUBGRAPH = "insert_sub_graph"
    UPDATE_NODE = "update_node"
    REMOVE_NODE = "remove_node"
    CONNECT_PAD = "connect_pad"
    DISCONNECT_PAD = "disconnect_pad"
    UPDATE_PAD = "update_pad"
    INSERT_INLINE_SUBGRAPH = "insert_inline_sub_graph"


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


class InlineSubGraphConnectionIn(BaseModel):
    from_node: str = Field(..., description="ID of the external source node")
    from_pad: str = Field(..., description="Handle ID of the external source pad")
    to_subgraph_pad: str = Field(..., description="ID of the subgraph sink pad to connect to")


class InlineSubGraphConnectionOut(BaseModel):
    from_subgraph_pad: str = Field(..., description="ID of the subgraph source pad to connect from")
    to_node: str = Field(..., description="ID of the external target node")
    to_pad: str = Field(..., description="Handle ID of the external target pad")


class InsertInlineSubGraphEdit(BaseModel):
    type: Literal[EditType.INSERT_INLINE_SUBGRAPH] = EditType.INSERT_INLINE_SUBGRAPH
    id: str | None = None
    subgraph_id: str | None = Field(
        default=None, description="Repository ID for this subgraph, if saved"
    )
    subgraph_name: str
    graph: "GraphEditorRepresentation"
    editor_position: tuple[float, float]
    editor_dimensions: tuple[float, float] | None = None
    editor_name: str
    inbound_connections: list[InlineSubGraphConnectionIn] = Field(
        default_factory=list,
        description="External sources to connect to subgraph sink pads at insert time",
    )
    outbound_connections: list[InlineSubGraphConnectionOut] = Field(
        default_factory=list,
        description="Subgraph source pads to connect to external sinks at insert time",
    )
    remove_node_ids: list[str] = Field(
        default_factory=list, description="Node IDs to remove after insertion"
    )


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
    value: Any = Field(..., description="New value for the pad")


Edit = Annotated[
    InsertNodeEdit
    | InsertSubGraphEdit
    | InsertInlineSubGraphEdit
    | UpdateNodeEdit
    | RemoveNodeEdit
    | ConnectPadEdit
    | DisconnectPadEdit
    | UpdatePadEdit,
    Field(
        discriminator="type", description="Type of edit to perform on the graph editor"
    ),
]


class GraphEditorRepresentation(BaseModel):
    nodes: list["NodeEditorRepresentation"]


K = TypeVar("K", bound=Node, covariant=True)


class GraphLibraryItem_Node(BaseModel, Generic[K]):
    type: Literal["node"] = "node"
    name: str = Field(..., description="Name of the node")
    node_type: Type[K] = Field(..., description="Class of the node", exclude=True)
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
    value: Any | None = None
    next_pads: list[PadReference]
    previous_pad: PadReference | None = None
    allowed_types: list[types.PadType] | None = None

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
