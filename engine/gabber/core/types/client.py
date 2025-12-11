from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic.types import Json
from typing import Any, Literal, Annotated
from enum import Enum as PyEnum
from ..types import pad_constraints


class String(BaseModel):
    type: Literal["string"] = "string"
    value: str


class Boolean(BaseModel):
    type: Literal["boolean"] = "boolean"
    value: bool


class Integer(BaseModel):
    type: Literal["integer"] = "integer"
    value: int


class Float(BaseModel):
    type: Literal["float"] = "float"
    value: float


class Trigger(BaseModel):
    type: Literal["trigger"] = "trigger"


class AudioClip(BaseModel):
    type: Literal["audio_clip"] = "audio_clip"
    transcription: str | None
    duration: float


class VideoClip(BaseModel):
    type: Literal["video_clip"] = "video_clip"
    duration: float
    frame_count: int


class ContextMessageContentItem_Image(BaseModel):
    width: int
    height: int
    handle: str
    timestamp: float | None


class ContextMessageContentItem_Audio(BaseModel):
    duration: float
    transcription: str | None
    handle: str
    start_timestamp: float | None


class ContextMessageContentItem_Video(BaseModel):
    width: int
    height: int
    duration: float
    handle: str
    frame_count: int
    start_timestamp: float | None


class ContextMessageContentItem(BaseModel):
    content_type: Literal["text", "image", "audio", "video"]
    text: str | None = None
    image: ContextMessageContentItem_Image | None = None
    audio: ContextMessageContentItem_Audio | None = None
    video: ContextMessageContentItem_Video | None = None


class ContextMessageRoleEnum(str, PyEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ContextMessageRole(BaseModel):
    type: Literal["context_message_role"] = "context_message_role"
    value: ContextMessageRoleEnum

    class Config:
        arbitrary_types_allowed = True


class ToolCall(BaseModel):
    call_id: str
    index: int
    name: str
    arguments: dict[str, Any]


class ContextMessage(BaseModel):
    type: Literal["context_message"] = "context_message"
    role: ContextMessageRole
    tool_calls: list[ToolCall]
    tool_call_id: str | None = None
    refusal: str | None = None
    content: list[ContextMessageContentItem]


class Enum(BaseModel):
    type: Literal["enum"] = "enum"
    value: str


class VisemeEnum(PyEnum):
    SILENCE = "SILENCE"
    PP = "PP"
    FF = "FF"
    TH = "TH"
    DD = "DD"
    kk = "KK"
    CH = "CH"
    SS = "SS"
    nn = "NN"
    RR = "RR"
    aa = "AA"
    E = "E"
    ih = "IH"
    oh = "OH"
    ou = "OU"


class Viseme(BaseModel):
    type: Literal["viseme"] = "viseme"
    value: VisemeEnum

    class Config:
        arbitrary_types_allowed = True

    def log_type(self) -> str:
        return "viseme"


class Secret(BaseModel):
    type: Literal["secret"] = "secret"
    secret_id: str
    name: str


class NodeReference(BaseModel):
    type: Literal["node_reference"] = "node_reference"
    node_id: str


class ToolDefinition(BaseModel):
    type: Literal["tool_definition"] = "tool_definition"
    name: str
    description: str
    parameters: dict[str, Any] | None = None
    destination: "ToolDefinitionDestination"


class ToolDefinitionDestination_Webhook_RetryPolicy(BaseModel):
    max_retries: int
    backoff_factor: float
    initial_delay_seconds: float


class ToolDefinitionDestination_Webhook(BaseModel):
    type: Literal["webhook"] = "webhook"
    url: str
    retry_policy: ToolDefinitionDestination_Webhook_RetryPolicy


class ToolDefinitionDestination_Client(BaseModel):
    type: Literal["client"] = "client"


ToolDefinitionDestination = Annotated[
    ToolDefinitionDestination_Client | ToolDefinitionDestination_Webhook,
    Field(discriminator="type"),
]


class List(BaseModel):
    type: Literal["list"] = "list"
    count: int
    items: list["ClientPadValue"]


class Object(BaseModel):
    type: Literal["object"] = "object"
    value: dict[str, Any]


ClientPadValue = (
    String
    | Integer
    | Float
    | Boolean
    | Trigger
    | AudioClip
    | VideoClip
    | List
    | ContextMessageRole
    | ContextMessage
    | Enum
    | Secret
    | NodeReference
    | ToolDefinition
    | Object
    | Viseme
    | None
)

DiscriminatedClientPadValue = Annotated[
    ClientPadValue,
    Field(discriminator="type"),
]
