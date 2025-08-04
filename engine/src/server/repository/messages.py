# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from core.editor import models

from .models import AppRunConnectionDetails, RepositoryApp, RepositorySubGraph


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


class CreateAppRunRequest(BaseModel):
    type: Literal["create_app_run"] = "create_app_run"
    graph: models.GraphEditorRepresentation


class DebugConnectionRequest(BaseModel):
    type: Literal["create_debug_connection"] = "create_debug_connection"
    app_run: str


Request = Annotated[
    SaveSubgraphRequest | SaveAppRequest | CreateAppRunRequest | DebugConnectionRequest,
    Field(discriminator="type", description="Request to perform on the graph editor"),
]


class GetAppResponse(BaseModel):
    type: Literal["get_app"] = "get_app"
    app: RepositoryApp


class SaveAppResponse(BaseModel):
    type: Literal["save_app"] = "save_app"
    app: RepositoryApp


class ListAppsResponse(BaseModel):
    type: Literal["list_apps"] = "list_apps"
    apps: list[RepositoryApp]


class GetSubgraphResponse(BaseModel):
    type: Literal["get_subgraph"] = "get_subgraph"
    sub_graph: RepositorySubGraph


class SaveSubgraphResponse(BaseModel):
    type: Literal["save_subgraph"] = "save_subgraph"
    sub_graph: RepositorySubGraph


class ListSubgraphsResponse(BaseModel):
    type: Literal["list_subgraphs"] = "list_subgraphs"
    sub_graphs: list[RepositorySubGraph]


class CreateAppRunResponse(BaseModel):
    type: Literal["create_app_run"] = "create_app_run"
    connection_details: AppRunConnectionDetails
    id: str


class DebugConnectionResponse(BaseModel):
    type: Literal["debug_connection"] = "debug_connection"
    connection_details: AppRunConnectionDetails
    graph: models.GraphEditorRepresentation


Response = Annotated[
    SaveSubgraphResponse
    | SaveAppResponse
    | ListAppsResponse
    | GetAppResponse
    | GetSubgraphResponse
    | ListSubgraphsResponse
    | CreateAppRunResponse
    | DebugConnectionResponse,
    Field(discriminator="type", description="Response from the graph editor"),
]
