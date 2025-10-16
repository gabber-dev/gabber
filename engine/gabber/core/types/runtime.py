# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from __future__ import annotations

import asyncio
import base64
from abc import abstractmethod, ABC
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, Literal, cast

import cv2
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, field_serializer

from . import pad_constraints


class BaseRuntimeType(ABC):
    def to_log_values(self) -> dict[str, str | float | int | bool]:
        return {"type": self.log_type()}

    @abstractmethod
    def log_type(self) -> str:
        raise NotImplementedError()


class Point(BaseModel, BaseRuntimeType):
    x: float
    y: float

    def log_type(self) -> str:
        return "point"


class BoundingBox(BaseModel, BaseRuntimeType):
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def log_type(self) -> str:
        return "bounding_box"


@dataclass
class AudioFrameData:
    data: NDArray[np.int16]
    sample_rate: int
    num_channels: int

    @property
    def duration(self) -> float:
        if self.sample_rate <= 0 or self.num_channels <= 0:
            raise ValueError(
                "Sample rate and number of channels must be greater than zero."
            )
        total_samples = self.data.size  # Total elements in the array
        if total_samples == 0:
            return 0.0
        if total_samples % self.num_channels != 0:
            raise ValueError(
                "Data size must not divisible by num_channels—possible data corruption."
            )
        return float(self.data.size) / float(self.sample_rate * self.num_channels)

    @property
    def fp32(self) -> NDArray[np.float32]:
        return self.data.astype(np.float32) / 32768.0

    @property
    def sample_count(self) -> int:
        return self.data.shape[1]

    def log_type(self) -> str:
        return "audio_frame_data"


@dataclass
class AudioFrame(BaseRuntimeType):
    original_data: AudioFrameData
    data_16000hz: AudioFrameData
    data_24000hz: AudioFrameData
    data_44100hz: AudioFrameData
    data_48000hz: AudioFrameData

    @staticmethod
    def silence(duration: float):
        """Create a silent audio frame of the given duration."""
        data_24000hz = np.zeros((1, int(duration * 24000)), dtype=np.int16)
        data_16000hz = np.zeros((1, int(duration * 16000)), dtype=np.int16)
        data_44100hz = np.zeros((1, int(duration * 44100)), dtype=np.int16)
        data_48000hz = np.zeros((1, int(duration * 48000)), dtype=np.int16)
        return AudioFrame(
            original_data=AudioFrameData(data_16000hz, 16000, 1),
            data_16000hz=AudioFrameData(data_16000hz, 16000, 1),
            data_24000hz=AudioFrameData(data_24000hz, 24000, 1),
            data_44100hz=AudioFrameData(data_44100hz, 44100, 1),
            data_48000hz=AudioFrameData(data_48000hz, 48000, 1),
        )

    def log_type(self) -> str:
        return "audio_frame"


class VideoFormat(Enum):
    RGBA = "RGBA"


@dataclass
class VideoFrame(BaseRuntimeType):
    data: np.ndarray  # (H,W,4) array of uint8 RGBA video data
    width: int
    height: int
    timestamp: float
    format: VideoFormat = VideoFormat.RGBA

    def to_base64_png(self) -> str:
        """Convert the video frame to a base64-encoded PNG image, scaled to max 384x384 pixels."""
        rgb_data = cv2.cvtColor(self.data, cv2.COLOR_RGBA2RGB)
        bgr_data = cv2.cvtColor(rgb_data, cv2.COLOR_RGB2BGR)

        _, buffer = cv2.imencode(".png", bgr_data)
        b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
        return b64

    @classmethod
    def black_frame(cls, width: int, height: int, timestamp: float) -> "VideoFrame":
        """Create a black video frame of the given width and height."""
        data = np.zeros((height, width, 4), dtype=np.uint8)
        return cls(data=data, width=width, height=height, timestamp=timestamp)

    def log_type(self) -> str:
        return "video_frame"

    def downsize(
        self,
        *,
        max_dimension: int | None = None,
        dimension_divisible_by: int | None = None,
        max_pixels: int | None = None,
    ) -> "VideoFrame":
        width = self.width
        height = self.height
        if max_dimension is not None:
            if width > max_dimension or height > max_dimension:
                scale = min(max_dimension / width, max_dimension / height)
                width = int(width * scale)
                height = int(height * scale)

        if max_pixels is not None and width * height > max_pixels:
            scale = (max_pixels / (width * height)) ** 0.5
            width = int(width * scale)
            height = int(height * scale)

        if dimension_divisible_by is not None:
            width = (width // dimension_divisible_by) * dimension_divisible_by
            height = (height // dimension_divisible_by) * dimension_divisible_by

        resized_data = cv2.resize(
            self.data, (width, height), interpolation=cv2.INTER_AREA
        )
        return VideoFrame(
            data=resized_data,
            width=width,
            height=height,
            timestamp=self.timestamp,
            format=self.format,
        )

    def crop(self, *, normalized_bbox: BoundingBox) -> "VideoFrame":
        x_min = int(normalized_bbox.x_min * self.width)
        y_min = int(normalized_bbox.y_min * self.height)
        x_max = int(normalized_bbox.x_max * self.width)
        y_max = int(normalized_bbox.y_max * self.height)
        x_min = max(0, min(self.width - 1, x_min))
        y_min = max(0, min(self.height - 1, y_min))
        x_max = max(0, min(self.width, x_max))
        y_max = max(0, min(self.height, y_max))
        if x_max <= x_min or y_max <= y_min:
            raise ValueError("Invalid bounding box for cropping.")

        cropped_data = self.data[y_min:y_max, x_min:x_max, :]
        return VideoFrame(
            data=cropped_data,
            width=cropped_data.shape[1],
            height=cropped_data.shape[0],
            timestamp=self.timestamp,
            format=self.format,
        )


@dataclass
class AudioClip(BaseRuntimeType):
    audio: list[AudioFrame]
    transcription: str | None = None

    @property
    def concatted_24000hz(self) -> NDArray[np.int16]:
        if not self.audio:
            return np.array([], dtype=np.int16)

        return np.concatenate([frame.data_24000hz.data for frame in self.audio], axis=1)

    @property
    def fp32_44100(self) -> NDArray[np.float32]:
        return np.concatenate([f.data_44100hz.fp32.flatten() for f in self.audio])

    @property
    def duration(self) -> float:
        if not self.audio:
            return 0.0

        total_duration = sum(frame.original_data.duration for frame in self.audio)
        return total_duration

    def log_type(self) -> str:
        return "audio_clip"


@dataclass
class VideoClip(BaseRuntimeType):
    video: list[VideoFrame]
    mp4_bytes: bytes | None = None

    @property
    def stacked_bgr_frames(self) -> np.ndarray:
        if not self.video:
            return np.array([], dtype=np.uint8)

        # converted to BGR format
        bgr_frames = [
            cv2.cvtColor(frame.data, cv2.COLOR_BGRA2BGR) for frame in self.video
        ]
        return np.stack(bgr_frames, axis=0)

    @property
    def duration(self) -> float:
        if not self.video:
            return 0.0

        first_timestamp = self.video[0].timestamp
        last_timestamp = self.video[-1].timestamp
        return last_timestamp - first_timestamp

    def log_type(self) -> str:
        return "video_clip"

    @property
    def estimated_fps(self) -> int:
        if len(self.video) < 2:
            return 1
        total_time = self.video[-1].timestamp - self.video[0].timestamp
        if total_time <= 0:
            return 1

        return int((len(self.video) - 1) / total_time)


@dataclass
class AVClip(BaseRuntimeType):
    video: VideoClip
    audio: AudioClip

    def log_type(self) -> str:
        return "av_clip"


@dataclass
class TextStream(BaseRuntimeType):
    def __init__(self):
        self._output_queue = asyncio.Queue[str | None]()

    def push_text(self, text: str):
        self._output_queue.put_nowait(text)

    def eos(self):
        self._output_queue.put_nowait(None)

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self._output_queue.get()
        if item is None:
            raise StopAsyncIteration

        return item

    def log_type(self) -> str:
        return "text_stream"


class ToolCall(BaseModel, BaseRuntimeType):
    call_id: str
    index: int
    name: str
    arguments: dict[str, Any]

    def log_type(self) -> str:
        return "tool_call"


class ToolDefinition(BaseModel, BaseRuntimeType):
    name: str
    description: str
    parameters: "Schema | None" = None

    def log_type(self) -> str:
        return "tool_definition"


class ContextMessageContentItem_Audio(BaseModel):
    type: Literal["audio"] = "audio"
    clip: AudioClip = Field(exclude=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ContextMessageContentItem_Video(BaseModel):
    type: Literal["video"] = "video"
    clip: VideoClip = Field(exclude=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ContextMessageContentItem_Image(BaseModel):
    type: Literal["image"] = "image"
    frame: VideoFrame = Field(exclude=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ContextMessageContentItem_Text(BaseModel):
    type: Literal["text"] = "text"
    content: str


ContextMessageContentItem = Annotated[
    ContextMessageContentItem_Audio
    | ContextMessageContentItem_Video
    | ContextMessageContentItem_Image
    | ContextMessageContentItem_Text,
    Field(discriminator="type"),
]


class ContextMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ContextMessage(BaseModel, BaseRuntimeType):
    role: ContextMessageRole
    content: list[ContextMessageContentItem]
    tool_calls: list[ToolCall]
    tool_call_id: str | None = None

    @field_serializer("content")
    def serialize_value(self, content: list[ContextMessageContentItem]):
        res: list = []
        for item in content:
            if isinstance(item, ContextMessageContentItem_Audio):
                continue
            elif isinstance(item, ContextMessageContentItem_Video):
                continue
            elif isinstance(item, ContextMessageContentItem_Text):
                res.append(item.model_dump(serialize_as_any=True))
        return res

    class Config:
        # Enable arbitrary types to allow Any
        arbitrary_types_allowed = True

    def log_type(self) -> str:
        return "context_message"


class ContextMessageContent_ToolCallDelta(BaseModel):
    index: int
    id: str | None
    name: str | None
    arguments: str | None


class Schema(BaseModel, BaseRuntimeType):
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

    def to_json_schema(self) -> dict[str, Any]:
        properties = {k: v.to_json_schema() for k, v in self.properties.items()}
        for d in self.defaults or {}:
            if self.defaults is None:
                continue
            if d in properties:
                properties[d]["default"] = self.defaults[d]
        return {
            "type": "object",
            "properties": properties,
            "required": self.required or [],
        }

    @classmethod
    def from_json_schema(cls, schema: dict[str, Any]) -> "Schema":
        properties: dict[
            str,
            pad_constraints.String
            | pad_constraints.Integer
            | pad_constraints.Float
            | pad_constraints.Boolean
            | pad_constraints.Object
            | pad_constraints.List,
        ] = {}
        for key, value in schema.get("properties", {}).items():
            type_ = value.get("type")
            if type_ == "string":
                properties[key] = pad_constraints.String()
            elif type_ == "integer":
                properties[key] = pad_constraints.Integer()
            elif type_ == "number":
                properties[key] = pad_constraints.Float()
            elif type_ == "boolean":
                properties[key] = pad_constraints.Boolean()
            elif type_ == "object":
                properties[key] = pad_constraints.Object()
            elif type_ == "array":
                properties[key] = pad_constraints.List(item_type_constraints=None)
            else:
                raise ValueError(f"Unsupported property type: {type_}")
        return cls(
            properties=properties,
            required=schema.get("required", []),
            defaults={
                k: v.get("default")
                for k, v in schema.get("properties", {}).items()
                if "default" in v
            },
        )

    def intersect(self, other: "Schema"):
        if not isinstance(other, Schema):
            return None
        properties: dict[
            str,
            pad_constraints.String
            | pad_constraints.Integer
            | pad_constraints.Float
            | pad_constraints.Boolean
            | pad_constraints.Object
            | pad_constraints.List,
        ] = {}
        defaults: dict[str, Any] = {}
        for d in self.defaults or {}:
            if self.defaults is None:
                continue
            defaults[d] = self.defaults[d]
        for key, value in self.properties.items():
            if key in other.properties:
                intersection = cast(pad_constraints.BasePadType, value).intersect(
                    cast(pad_constraints.BasePadType, other.properties[key])
                )
                intersection = cast(
                    pad_constraints.String
                    | pad_constraints.Integer
                    | pad_constraints.Float
                    | pad_constraints.Boolean
                    | None,
                    intersection,
                )
                if intersection is not None:
                    properties[key] = intersection
        my_required = set(self.required or [])
        other_required = set(other.required or [])
        return Schema(
            properties=properties,
            required=list(my_required | other_required),
            defaults=defaults,
        )

    def log_type(self) -> str:
        return "schema"


class Trigger(BaseModel, BaseRuntimeType):
    def log_type(self) -> str:
        return "trigger"


class NodeReference(BaseModel):
    node_id: str
    node_type: str


@dataclass
class ContextMessageContent_ChoiceDelta:
    content: str | None
    refusal: str | None
    usage: dict[str, int] | None
    role: ContextMessageRole | None
    tool_calls: list[ContextMessageContent_ToolCallDelta] | None


@dataclass
class ContextMessageDeltaStream:
    def __init__(self):
        self._output_queue = asyncio.Queue[ContextMessageContent_ChoiceDelta | None]()

    def push_delta(self, message: ContextMessageContent_ChoiceDelta):
        self._output_queue.put_nowait(message)

    def eos(self):
        self._output_queue.put_nowait(None)

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self._output_queue.get()
        if item is None:
            raise StopAsyncIteration

        return item


RuntimePadValuePrimitive = str | int | float | bool


RuntimePadValue = (
    RuntimePadValuePrimitive
    | Enum
    | Trigger
    | AudioClip
    | VideoClip
    | AVClip
    | TextStream
    | AudioFrame
    | VideoFrame
    | ToolCall
    | ContextMessage
    | ToolDefinition
    | Schema
    | NodeReference
    | None
    | list["RuntimePadValue"]
)
