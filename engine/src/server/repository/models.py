# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import datetime
from pydantic import BaseModel
from core.editor import models


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
