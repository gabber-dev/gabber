# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from pydantic import BaseModel, Field
from typing import Literal, Annotated
from core.editor import models
from .models import RepositorySubGraph, RepositoryApp


class SaveSubgraphRequest(BaseModel):
    type: Literal["save_subgraph"] = "save_subgraph"
    id: str | None = None
    name: str
    graph: models.GraphEditorRepresentation


class SaveAppRequest(BaseModel):
    type: Literal["save_app"] = "save_app"
    id: str | None = None
    name: str
    graph: models.GraphEditorRepresentation


Request = Annotated[
    SaveSubgraphRequest | SaveAppRequest,
    Field(discriminator="type", description="Request to perform on the graph editor"),
]


class GetAppResponse(BaseModel):
    type: Literal["get_app_response"] = "get_app_response"
    app: RepositoryApp


class SaveAppResponse(BaseModel):
    type: Literal["save_app_response"] = "save_app_response"
    app: RepositoryApp


class ListAppsResponse(BaseModel):
    type: Literal["list_apps_response"] = "list_apps_response"
    apps: list[RepositoryApp]


class GetSubgraphResponse(BaseModel):
    type: Literal["get_subgraph_response"] = "get_subgraph_response"
    sub_graph: RepositorySubGraph


class SaveSubgraphResponse(BaseModel):
    type: Literal["save_subgraph_response"] = "save_subgraph_response"
    sub_graph: RepositorySubGraph


class ListSubgraphsResponse(BaseModel):
    type: Literal["list_subgraphs_response"] = "list_subgraphs_response"
    sub_graphs: list[RepositorySubGraph]


Response = Annotated[
    SaveSubgraphResponse
    | SaveAppResponse
    | ListAppsResponse
    | GetAppResponse
    | GetSubgraphResponse
    | ListSubgraphsResponse,
    Field(discriminator="type", description="Response from the graph editor"),
]
