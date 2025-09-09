from dataclasses import dataclass
from typing import Annotated, Literal
from ..generated import runtime
from pydantic import Field


@dataclass
class ConnectionDetails:
    token: str
    url: str


@dataclass
class SubscribeParams:
    output_or_publish_node: str


ConnectionState = Literal[
    "disconnected", "connecting", "waiting_for_engine", "connected"
]


RuntimeRequestPayload = Annotated[
    runtime.RuntimeRequestPayloadGetValue
    | runtime.RuntimeRequestPayloadLockPublisher
    | runtime.RuntimeRequestPayloadPushValue
    | runtime.RuntimeRequestPayloadListMCPServers,
    Field(discriminator="type"),
]

RuntimeResponsePayload = Annotated[
    runtime.RuntimeResponsePayloadGetValue
    | runtime.RuntimeResponsePayloadLockPublisher
    | runtime.RuntimeResponsePayloadPushValue
    | runtime.RuntimeResponsePayloadListMCPServers,
    Field(discriminator="type"),
]

PadValue = Annotated[
    runtime.PadValueString
    | runtime.PadValueInteger
    | runtime.PadValueFloat
    | runtime.PadValueBoolean
    | runtime.PadValueTrigger
    | runtime.PadValueAudioClip
    | runtime.PadValueVideoClip,
    Field(discriminator="type"),
]
