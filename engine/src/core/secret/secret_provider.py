# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import datetime
from abc import ABC, abstractmethod

from pydantic import BaseModel


class SecretProvider(ABC):
    @abstractmethod
    async def list_secrets(self) -> list["PublicSecret"]:
        """List all available secrets."""
        pass

    @abstractmethod
    async def resolve_secret(self, id: str) -> str:
        """Resolve a secret by its name."""
        pass


class PublicSecret(BaseModel):
    updated_at: datetime.datetime
    created_at: datetime.datetime
    id: str
    name: str
