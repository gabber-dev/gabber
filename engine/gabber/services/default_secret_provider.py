# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from gabber.core import secret
import logging
import os
import aiofiles
import datetime


class DefaultSecretProvider(secret.SecretProvider):
    def __init__(self):
        self.secret_file = os.environ["GABBER_SECRET_FILE"]

    async def list_secrets(self) -> list[secret.PublicSecret]:
        secrets = await self._read_secrets()
        return [
            secret.PublicSecret(
                name=key,
                id=key,
                updated_at=datetime.datetime.now(),
                created_at=datetime.datetime.now(),
            )
            for key, _ in secrets.items()
        ]

    async def resolve_secret(self, id: str) -> str:
        if not id:
            return ""

        secrets = await self._read_secrets()
        if id in secrets:
            return secrets[id]
        raise KeyError(f"Secret with id '{id}' not found.")

    async def _read_secrets(self) -> dict[str, str]:
        secrets = {}
        if not os.path.exists(self.secret_file):
            logging.warning(f"Secret file {self.secret_file} does not exist.")
            return {}

        async with aiofiles.open(self.secret_file, mode="r") as f:
            async for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    secrets[key] = value
        return secrets
