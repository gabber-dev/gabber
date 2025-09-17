# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from abc import ABC, abstractmethod

from ..editor.models import GraphLibraryItem


class GraphLibrary(ABC):
    @abstractmethod
    async def list_items(self) -> list[GraphLibraryItem]:
        raise NotImplementedError("list_items must be implemented by subclasses")
