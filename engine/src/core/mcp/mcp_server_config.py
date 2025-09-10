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
    args: list[str]


MCPLocalTransport = Annotated[
    MCPTransportSTDIO | MCPTransportSSE, Field(discriminator="type")
]


class MCPTransportDatachannelProxy(BaseModel):
    type: Literal["datachannel_proxy"] = "datachannel_proxy"
    local_transport: MCPLocalTransport


MCPTransport = Annotated[
    MCPTransportDatachannelProxy | MCPTransportSTDIO | MCPTransportSTDIO,
    Field(discriminator="type"),
]


class MCPServer(BaseModel):
    name: str
    transport: "MCPTransport"
