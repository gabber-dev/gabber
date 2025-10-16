from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Literal, Annotated


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


class ContextMessage(BaseModel):
    type: Literal["context_message"] = "context_message"
    role: str
    content: list[ContextMessageContentItem]


class List(BaseModel):
    type: Literal["list"] = "list"
    count: int
    items: list[Any]


ClientPadValue = (
    String
    | Integer
    | Float
    | Boolean
    | Trigger
    | AudioClip
    | VideoClip
    | List
    | ContextMessage
    | None
)

DiscriminatedClientPadValue = Annotated[
    ClientPadValue,
    Field(discriminator="type"),
]
