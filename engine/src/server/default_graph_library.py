# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from core import graph
from core.editor import models
from nodes import ALL_NODES


class DefaultGraphLibrary(graph.GraphLibrary):
    async def list_items(self) -> list[models.GraphLibraryItem]:
        node_items: list[models.GraphLibraryItem] = [
            models.GraphLibraryItem_Node(
                node_type=n,
                name=n.__name__,
                description=n.get_description(),
                metadata=n.get_metadata(),
            )
            for n in ALL_NODES
        ]

        return node_items
