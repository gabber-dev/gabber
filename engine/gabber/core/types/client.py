from __future__ import annotations

from pydantic import BaseModel, Field
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
    transcript: str
    duration: float


class VideoClip(BaseModel):
    type: Literal["video_clip"] = "video_clip"
    duration: float


class ContextMessageContentItem_Image(BaseModel):
    width: int
    height: int
    handle: str


class ContextMessageContentItem_Audio(BaseModel):
    duration: float
    transcription: str | None
    handle: str


class ContextMessageContentItem_Video(BaseModel):
    width: int
    height: int
    duration: float
    handle: str


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


class ContextMessage(BaseModel):
    type: Literal["context_message"] = "context_message"
    role: ContextMessageRole
    content: list[ContextMessageContentItem]


class Enum(BaseModel):
    type: Literal["enum"] = "enum"
    value: str


class Secret(BaseModel):
    type: Literal["secret"] = "secret"
    secret_id: str
    name: str


class NodeReference(BaseModel):
    type: Literal["node_reference"] = "node_reference"
    node_id: str


class Schema(BaseModel):
    type: Literal["schema"] = "schema"
    properties: dict[
        str,
        pad_constraints.String
        | pad_constraints.Integer
        | pad_constraints.Float
        | pad_constraints.Boolean
        | pad_constraints.Object
        | pad_constraints.List,
    ]
    required: list[str] | None = None
    defaults: dict[str, Any] | None = None


class ToolDefinition(BaseModel):
    type: Literal["tool_definition"] = "tool_definition"
    name: str
    description: str
    parameters: "Schema | None" = None


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
    | Schema
    | Object
    | None
)

DiscriminatedClientPadValue = Annotated[
    ClientPadValue,
    Field(discriminator="type"),
]
