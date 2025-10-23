# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import datetime
from pydantic import BaseModel
from gabber.core.editor import models


class RepositorySubGraph(BaseModel):
    id: str
    name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    graph: models.GraphEditorRepresentation


class RepositoryApp(BaseModel):
    id: str
    name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    graph: models.GraphEditorRepresentation


class AppRunConnectionDetails(BaseModel):
    url: str
    token: str


class AppExport(BaseModel):
    app: RepositoryApp
    subgraphs: list[RepositorySubGraph]


class SubGraphExport(BaseModel):
    subgraph: RepositorySubGraph
    nested_subgraphs: list[RepositorySubGraph]
