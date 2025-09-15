# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from gabber.core.editor import models

from .models import (
    AppRunConnectionDetails,
    RepositoryApp,
    RepositorySubGraph,
    AppExport,
)


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
    run_id: str
    graph: models.GraphEditorRepresentation


class DebugConnectionRequest(BaseModel):
    type: Literal["create_debug_connection"] = "create_debug_connection"
    run_id: str


class MCPProxyConnectionRequest(BaseModel):
    type: Literal["mcp_proxy_connection"] = "mcp_proxy_connection"
    run_id: str


class ImportAppRequest(BaseModel):
    type: Literal["import_app"] = "import_app"
    export: AppExport


Request = Annotated[
    SaveSubgraphRequest
    | SaveAppRequest
    | CreateAppRunRequest
    | DebugConnectionRequest
    | ImportAppRequest
    | MCPProxyConnectionRequest,
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


class ListAppRunsResponse(BaseModel):
    type: Literal["list_app_runs"] = "list_app_runs"
    runs: list[str]


class DebugConnectionResponse(BaseModel):
    type: Literal["debug_connection"] = "debug_connection"
    connection_details: AppRunConnectionDetails
    graph: models.GraphEditorRepresentation


class MCPProxyConnectionResponse(BaseModel):
    type: Literal["mcp_proxy_connection"] = "mcp_proxy_connection"
    connection_details: AppRunConnectionDetails


class ImportAppResponse(BaseModel):
    type: Literal["import_app"] = "import_app"


class ExportAppResponse(BaseModel):
    type: Literal["export_app"] = "export_app"
    export: AppExport


Response = Annotated[
    SaveSubgraphResponse
    | SaveAppResponse
    | ListAppsResponse
    | GetAppResponse
    | GetSubgraphResponse
    | ListSubgraphsResponse
    | CreateAppRunResponse
    | ListAppRunsResponse
    | DebugConnectionResponse
    | ImportAppResponse
    | ExportAppResponse
    | MCPProxyConnectionResponse,
    Field(discriminator="type", description="Response from the graph editor"),
]
