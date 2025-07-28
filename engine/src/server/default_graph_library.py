# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from core import graph
from core.editor import models


class DefaultGraphLibrary(graph.GraphLibrary):
    async def list_items(self) -> list[models.GraphLibraryItem]:
        return []
