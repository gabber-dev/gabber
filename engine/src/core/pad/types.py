# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from core.secret import PublicSecret


class BasePadType(BaseModel):
    def intersect(self, other: "BasePadType") -> "BasePadType | None":
        if isinstance(other, type(self)):
            return self
        return None


class String(BasePadType):
    type: Literal["string"] = "string"
    max_length: int | None = None
    min_length: int | None = None

    def intersect(self, other: "BasePadType"):
        if not isinstance(other, String):
            return None

        return String(
            type=self.type,
            max_length=(
                min(self.max_length, other.max_length)
                if self.max_length is not None and other.max_length is not None
                else None
            ),
            min_length=(
                max(self.min_length, other.min_length)
                if self.min_length is not None and other.min_length is not None
                else None
            ),
        )


class Enum(BasePadType):
    type: Literal["enum"] = "enum"
    options: list[str] | None = None

    def intersect(self, other: "BasePadType"):
        if not isinstance(other, Enum):
            return None

        if self.options is None and other.options is None:
            return Enum(type=self.type, options=None)

        if self.options is not None and other.options is not None:
            common_values = set(self.options).intersection(set(other.options))
            return Enum(
                type=self.type,
                options=list(common_values) if common_values else None,
            )

        if self.options is not None:
            return Enum(
                type=self.type,
                options=self.options,
            )
        if other.options is not None:
            return Enum(
                type=self.type,
                options=other.options,
            )

        raise ValueError("Unexpected state.")


class Secret(BasePadType):
    type: Literal["secret"] = "secret"
    options: list[PublicSecret] = []

    def intersect(self, other: "BasePadType"):
        if not isinstance(other, Secret):
            return None

        secret_lookup: dict[str, PublicSecret] = {
            secret.id: secret for secret in self.options
        }
        intersected_options: list[PublicSecret] = []
        for option in other.options:
            if option.id in secret_lookup:
                intersected_options.append(secret_lookup[option.id])
        return Secret(
            type=self.type,
            options=intersected_options,
        )


class Integer(BasePadType):
    type: Literal["integer"] = "integer"
    maximum: int | None = None
    minimum: int | None = None

    def intersect(self, other: "BasePadType"):
        if not isinstance(other, Integer):
            return None
        return Integer(
            type=self.type,
            maximum=(
                min(self.maximum, other.maximum)
                if self.maximum is not None and other.maximum is not None
                else None
            ),
            minimum=(
                max(self.minimum, other.minimum)
                if self.minimum is not None and other.minimum is not None
                else None
            ),
        )


class Float(BasePadType):
    type: Literal["float"] = "float"
    maximum: float | None = None
    minimum: float | None = None

    def intersect(self, other: "BasePadType"):
        if not isinstance(other, Float):
            return None
        return Float(
            type=self.type,
            maximum=(
                min(self.maximum, other.maximum)
                if self.maximum is not None and other.maximum is not None
                else None
            ),
            minimum=(
                max(self.minimum, other.minimum)
                if self.minimum is not None and other.minimum is not None
                else None
            ),
        )


class BoundingBox(BasePadType):
    type: Literal["bounding_box"] = "bounding_box"


class Point(BasePadType):
    type: Literal["point"] = "point"


class Boolean(BasePadType):
    type: Literal["boolean"] = "boolean"


class Audio(BasePadType):
    type: Literal["audio"] = "audio"


class Video(BasePadType):
    type: Literal["video"] = "video"


class Trigger(BasePadType):
    type: Literal["trigger"] = "trigger"


class AudioClip(BasePadType):
    type: Literal["audio_clip"] = "audio_clip"


class VideoClip(BasePadType):
    type: Literal["video_clip"] = "video_clip"


class AVClip(BasePadType):
    type: Literal["av_clip"] = "av_clip"


class TextStream(BasePadType):
    type: Literal["text_stream"] = "text_stream"


class ContextMessage(BasePadType):
    type: Literal["context_message"] = "context_message"


class ContextMessageRole(BasePadType):
    type: Literal["context_message_role"] = "context_message_role"


class List(BasePadType):
    type: Literal["list"] = "list"
    max_length: int | None = None
    item_type_constraints: list["BasePadType"] | None

    def intersect(self, other: "BasePadType"):
        if not isinstance(other, List):
            return None
        return List(
            type=self.type,
            max_length=(
                min(self.max_length, other.max_length)
                if self.max_length is not None and other.max_length is not None
                else None
            ),
            item_type_constraints=INTERSECTION(
                self.item_type_constraints, other.item_type_constraints
            ),
        )


class Schema(BasePadType):
    type: Literal["schema"] = "schema"


class Object(BasePadType):
    type: Literal["object"] = "object"
    object_schema: dict[str, Any] | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def intersect(self, other: "BasePadType"):
        if not isinstance(other, Object):
            return None

        if self.object_schema is None and other.object_schema is None:
            return Object(object_schema=None)

        if self.object_schema is None:
            return Object(object_schema=other.object_schema)

        if other.object_schema is None:
            return Object(object_schema=self.object_schema)

        new_schema = {}
        for key, value in self.object_schema.items():
            if key in other.object_schema:
                # TODO: handle full intersection logic with constraints and whatnot
                new_schema[key] = value

        return Object(object_schema=new_schema) if new_schema else None


class NodeReference(BasePadType):
    type: Literal["node_reference"] = "node_reference"
    node_types: list[str]

    def intersect(self, other: BasePadType):
        if not isinstance(other, NodeReference):
            return None

        interection_set = set(self.node_types).intersection(set(other.node_types))
        if len(interection_set) == 0:
            return None

        return NodeReference(node_types=list(interection_set))


PadType = Annotated[
    String
    | Integer
    | Float
    | Boolean
    | Enum
    | Secret
    | BoundingBox
    | Point
    | Audio
    | Video
    | Trigger
    | AudioClip
    | VideoClip
    | AVClip
    | TextStream
    | ContextMessage
    | ContextMessageRole
    | List
    | Schema
    | Object
    | NodeReference,
    Field(discriminator="type"),
]


def INTERSECTION(
    set_1: list[BasePadType] | None, set_2: list[BasePadType] | None
) -> list[BasePadType] | None:
    if set_1 is None:
        return set_2
    if set_2 is None:
        return set_1

    result: list[BasePadType] = []
    for item_1 in set_1:
        for item_2 in set_2:
            intersection = item_1.intersect(item_2)
            if intersection is not None:
                result.append(intersection)

    return result


def EQUALS(set_1: list[BasePadType] | None, set_2: list[BasePadType] | None) -> bool:
    """
    Check if two lists of PadDataTypeDefinition objects are equal.

    Two sets are considered equal if:
    1. Both are None
    2. Both have the same length and contain equivalent elements
    """
    # Handle None cases
    if set_1 is None and set_2 is None:
        return True
    if set_1 is None or set_2 is None:
        return False

    # Check if lengths are different
    if len(set_1) != len(set_2):
        return False

    # For each item in set_1, find a matching item in set_2
    set_2_matched = [False] * len(set_2)

    for item_1 in set_1:
        found_match = False
        for i, item_2 in enumerate(set_2):
            if not set_2_matched[i] and _are_equivalent(item_1, item_2):
                set_2_matched[i] = True
                found_match = True
                break

        if not found_match:
            return False

    return True


def _are_equivalent(item_1: BasePadType, item_2: BasePadType) -> bool:
    """
    Check if two PadDataTypeDefinition objects are equivalent.

    Two items are equivalent if they have the same type and all their properties match.
    """
    # Check if they're the same type
    if type(item_1) is not type(item_2):
        return False

    # Use Pydantic's model comparison - this will compare all fields
    return item_1 == item_2


# TODO handle more complex types like List, Object, etc.
def json_schema_to_types(
    json_schema: dict[str, Any],
) -> dict[str, BasePadType]:
    res: dict[str, BasePadType] = {}

    if "type" not in json_schema:
        raise ValueError("JSON schema must have a 'type' key at the root level.")

    if json_schema["type"] != "object":
        raise ValueError(
            f"Expected 'object' type at the root of JSON schema, got '{json_schema['type']}'."
        )

    if "properties" not in json_schema:
        raise ValueError("JSON schema must have a 'properties' key.")

    properties = json_schema["properties"]
    if not isinstance(properties, dict):
        raise ValueError(
            f"Expected a dictionary for 'properties' in JSON schema, got {type(properties).__name__}."
        )

    for key, value in properties.items():
        if not isinstance(value, dict):
            raise ValueError(
                f"Expected a dictionary for property '{key}' in JSON schema, got {type(value).__name__}."
            )

        if "type" not in value:
            raise ValueError(f"Property '{key}' in JSON schema must have a 'type' key.")

        type_ = value["type"]
        if type_ == "string":
            res[key] = String(
                type=type_,
                max_length=value.get("maxLength"),
                min_length=value.get("minLength"),
            )
        elif type_ == "integer":
            res[key] = Integer(
                type=type_,
                maximum=value.get("maximum"),
                minimum=value.get("minimum"),
            )
        elif type_ == "float":
            res[key] = Float(
                type=type_,
                maximum=value.get("maximum"),
                minimum=value.get("minimum"),
            )
        elif type_ == "boolean":
            res[key] = Boolean(type=type_)

    return res
