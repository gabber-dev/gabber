# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from enum import Enum
from typing import Annotated, Literal
from ..pad.types import PadType

from pydantic import BaseModel, Field

from .models import (
    Edit,
    GraphEditorRepresentation,
    GraphLibraryItem,
    EligibleLibraryItem,
)


class RequestType(str, Enum):
    GET_NODE_LIBRARY = "get_node_library"
    QUERY_ELIGIBLE_NODE_LIBRARY_ITEMS = "query_eligible_node_library_items"
    LOAD_FROM_SNAPSHOT = "load_from_snapshot"
    EDIT = "edit"


class LoadFromSnapshotRequest(BaseModel):
    type: Literal[RequestType.LOAD_FROM_SNAPSHOT] = RequestType.LOAD_FROM_SNAPSHOT
    graph: GraphEditorRepresentation
    req_id: str


class GetNodeLibraryRequest(BaseModel):
    type: Literal[RequestType.GET_NODE_LIBRARY] = RequestType.GET_NODE_LIBRARY
    req_id: str
    filter: str | None = Field(
        default=None, description="Filter for node types (optional)"
    )
    include_metadata: bool = Field(
        default=False, description="Whether to include metadata in the response"
    )


class EditRequest(BaseModel):
    type: Literal[RequestType.EDIT] = RequestType.EDIT
    req_id: str
    edits: list[Edit] = Field(
        default_factory=list, description="Edit requests to perform on the graph editor"
    )


class QueryEligibleNodeLibraryItemsRequest(BaseModel):
    type: Literal[RequestType.QUERY_ELIGIBLE_NODE_LIBRARY_ITEMS] = (
        RequestType.QUERY_ELIGIBLE_NODE_LIBRARY_ITEMS
    )
    req_id: str
    source_node: str
    source_pad: str


Request = Annotated[
    GetNodeLibraryRequest
    | EditRequest
    | LoadFromSnapshotRequest
    | QueryEligibleNodeLibraryItemsRequest,
    Field(discriminator="type", description="Request to perform on the graph editor"),
]


class ResponseType(str, Enum):
    EDIT = "edit"
    LOAD_FROM_SNAPSHOT = "load_from_snapshot"
    NODE_LIBRARY = "node_library"
    QUERY_ELIGIBLE_NODE_LIBRARY_ITEMS = "query_eligible_node_library_items"


class EditResponse(BaseModel):
    type: Literal[ResponseType.EDIT] = ResponseType.EDIT
    req_id: str
    graph: GraphEditorRepresentation = Field(
        ...,
        description="Full graph representation including all nodes and their connections",
    )


class LoadFromSnapshotResponse(BaseModel):
    type: Literal[ResponseType.LOAD_FROM_SNAPSHOT] = ResponseType.LOAD_FROM_SNAPSHOT
    req_id: str
    graph: GraphEditorRepresentation = Field(
        ...,
        description="Full graph representation including all nodes and their connections",
    )


class NodeLibraryResponse(BaseModel):
    type: Literal[ResponseType.NODE_LIBRARY] = ResponseType.NODE_LIBRARY
    req_id: str
    node_library: list[GraphLibraryItem] = Field(
        default_factory=list, description="List of available nodes in the library"
    )


class QueryEligibleNodeLibraryItemsResponse(BaseModel):
    type: Literal[ResponseType.QUERY_ELIGIBLE_NODE_LIBRARY_ITEMS] = (
        ResponseType.QUERY_ELIGIBLE_NODE_LIBRARY_ITEMS
    )
    req_id: str
    direct_eligible_items: list[EligibleLibraryItem] = Field(
        default_factory=list, description="List of eligible items from the node library"
    )
    autoconvert_eligible_items: list[GraphLibraryItem] = Field(
        default_factory=list,
        description="List of autoconvert eligible items from the node library",
    )


Response = Annotated[
    EditResponse
    | LoadFromSnapshotResponse
    | NodeLibraryResponse
    | QueryEligibleNodeLibraryItemsResponse,
    Field(discriminator="type", description="Response from the graph editor"),
]


class DummyModel(BaseModel):
    request: Request
    response: Response
    edit: Edit
    pad_type: PadType
