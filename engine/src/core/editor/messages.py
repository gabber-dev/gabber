# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .models import Edit, GraphEditorRepresentation, GraphLibraryItem


class RequestType(str, Enum):
    GET_NODE_LIBRARY = "get_node_library"
    LOAD_FROM_SNAPSHOT = "load_from_snapshot"
    EDIT = "edit"


class LoadFromSnapshotRequest(BaseModel):
    type: Literal[RequestType.LOAD_FROM_SNAPSHOT] = RequestType.LOAD_FROM_SNAPSHOT
    graph: GraphEditorRepresentation


class GetNodeLibraryRequest(BaseModel):
    type: Literal[RequestType.GET_NODE_LIBRARY] = RequestType.GET_NODE_LIBRARY
    filter: str | None = Field(
        default=None, description="Filter for node types (optional)"
    )
    include_metadata: bool = Field(
        default=False, description="Whether to include metadata in the response"
    )


class EditRequest(BaseModel):
    type: Literal[RequestType.EDIT] = RequestType.EDIT
    edit: Edit = Field(
        discriminator="type", description="Edit request to perform on the graph editor"
    )


Request = Annotated[
    GetNodeLibraryRequest | EditRequest | LoadFromSnapshotRequest,
    Field(discriminator="type", description="Request to perform on the graph editor"),
]


class ResponseType(str, Enum):
    FULL_GRAPH = "full_graph"
    NODE_LIBRARY = "node_library"


class FullGraphResponse(BaseModel):
    type: Literal[ResponseType.FULL_GRAPH] = ResponseType.FULL_GRAPH
    graph: GraphEditorRepresentation = Field(
        ...,
        description="Full graph representation including all nodes and their connections",
    )


class NodeLibraryResponse(BaseModel):
    type: Literal[ResponseType.NODE_LIBRARY] = ResponseType.NODE_LIBRARY
    node_library: list[GraphLibraryItem] = Field(
        default_factory=list, description="List of available nodes in the library"
    )


class Response(BaseModel):
    response: FullGraphResponse | NodeLibraryResponse = Field(
        discriminator="type", description="Change to apply to the graph editor"
    )
