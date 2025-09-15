# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from pydantic import BaseModel, Field
from typing import Annotated, Literal


class MCPServerConfig(BaseModel):
    servers: list["MCPServer"]


class MCPTransportSSE(BaseModel):
    type: Literal["sse"] = "sse"
    url: str


class MCPTransportSTDIO(BaseModel):
    type: Literal["stdio"] = "stdio"
    command: str
    cwd: str | None = None
    args: list[str]
    env: dict[str, str] | None = None


MCPLocalTransport = Annotated[
    MCPTransportSTDIO | MCPTransportSSE, Field(discriminator="type")
]


MCPTransport = Annotated[
    MCPTransportSTDIO | MCPTransportSTDIO,
    Field(discriminator="type"),
]


class MCPServer(BaseModel):
    name: str
    transport: "MCPTransport"
