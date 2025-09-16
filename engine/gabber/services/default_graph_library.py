# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import os
import logging
from pathlib import Path

import aiofiles

from gabber.core import graph
from gabber.core.editor import models
from gabber.nodes import ALL_NODES


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
            if n.get_type()
            != "SubGraph"  # SubGraph node should not be listed as a library item
        ]

        try:
            user_sub_graphs = await self._get_user_sub_graphs()
        except Exception as e:
            user_sub_graphs = []
        default_sub_graphs = await self._get_default_sub_graphs()

        return node_items + user_sub_graphs + default_sub_graphs

    async def _get_user_sub_graphs(self) -> list[models.GraphLibraryItem]:
        sub_graphs: list[models.GraphLibraryItem] = []
        rep_dir = os.environ["GABBER_REPOSITORY_DIR"]
        dir_path = Path(rep_dir) / "sub_graph"
        for file_path in dir_path.glob("*.json"):
            async with aiofiles.open(str(file_path), "r") as f:
                content = await f.read()
                item = models.GraphLibraryItem_SubGraph.model_validate_json(content)
                item.editable = True
                sub_graphs.append(item)
        return sub_graphs

    async def _get_default_sub_graphs(self) -> list[models.GraphLibraryItem]:
        sub_graphs: list[models.GraphLibraryItem] = []
        dir_path = Path(__file__).parent.parent.parent / "data" / "sub_graph"
        for file_path in dir_path.glob("*.json"):
            async with aiofiles.open(str(file_path), "r") as f:
                content = await f.read()
            item = models.GraphLibraryItem_SubGraph.model_validate_json(content)
            item.editable = False
            sub_graphs.append(item)
        return sub_graphs
