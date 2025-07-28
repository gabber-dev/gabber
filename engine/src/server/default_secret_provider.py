# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from core import secret


class DefaultSecretProvider(secret.SecretProvider):
    async def list_secrets(self) -> list[secret.PublicSecret]:
        return []

    async def resolve_secret(self, id: str) -> str:
        return ""
