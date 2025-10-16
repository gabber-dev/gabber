# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import Any, cast

from pydantic import BaseModel

from .. import node, pad
from ..types import runtime, pad_constraints

from .models import NodeEditorRepresentation, PadEditorRepresentation, PadReference


def serialize_pad_value(v: Any | None):
    if v is None:
        return None
    elif isinstance(v, (int, float, str, bool)):
        return v
    elif isinstance(v, dict):
        return v
    elif isinstance(v, list):
        return [serialize_pad_value(item) for item in v]
    elif isinstance(v, BaseModel):
        return v.model_dump(serialize_as_any=True)
    elif isinstance(v, node.Node):
        return v.id


def deserialize_pad_value(
    tc: pad_constraints.BasePadType,
    v: Any | None,
):
    if isinstance(tc, pad_constraints.Trigger):
        return runtime.Trigger()
    if isinstance(v, str | float | int):
        return v
    elif isinstance(v, BaseModel):
        return v
    elif isinstance(v, dict):
        if isinstance(tc, pad_constraints.ContextMessage):
            return runtime.ContextMessage.model_validate(v)
        elif isinstance(tc, pad_constraints.Object):
            return v
        elif isinstance(tc, pad_constraints.Schema):
            return runtime.Schema.model_validate(v)
        elif isinstance(tc, pad_constraints.BoundingBox):
            return runtime.BoundingBox.model_validate(v)
        elif isinstance(tc, pad_constraints.Point):
            return runtime.Point.model_validate(v)
    elif isinstance(v, list):
        if not isinstance(tc, pad_constraints.List):
            logging.error(
                f"Expected List type constraint for list deserialization, got {type(tc)}"
            )
            return None
        list_types = tc.item_type_constraints
        if not list_types or len(list_types) != 1:
            logging.error(
                f"List type constraints: {list_types}, value: {v}, type_constraints: {tc}"
            )
            return None

        items = [deserialize_pad_value(list_types[0], item) for item in v]
        return items


def pad_editor_rep(p: pad.Pad):
    value: Any | None = None
    if isinstance(p, pad.PropertyPad):
        value = serialize_pad_value(p.get_value())
    next_pads: list[PadReference] = []
    if isinstance(p, pad.SourcePad):
        next_pads = [
            PadReference(node=next_pad.get_owner_node().id, pad=next_pad.get_id())
            for next_pad in p.get_next_pads()
        ]

    previous_pad: PadReference | None = None
    if isinstance(p, pad.SinkPad):
        prev_pad = p.get_previous_pad()
        if prev_pad:
            previous_pad = PadReference(
                node=prev_pad.get_owner_node().id, pad=prev_pad.get_id()
            )

    # TODO: remove this cast. BasePadType is used for covariance elsewhere
    # but pydantic needs the Annotated PadType for serialization
    allowed_types: list[pad_constraints.PadType] | None = cast(
        list[pad_constraints.PadType], p.get_type_constraints()
    )
    default_allowed_types: list[pad_constraints.PadType] | None = cast(
        list[pad_constraints.PadType], p.get_default_type_constraints()
    )
    return PadEditorRepresentation(
        id=p.get_id(),
        group=p.get_group(),
        type=p.get_editor_type(),
        value=value,
        next_pads=next_pads,
        previous_pad=previous_pad,
        allowed_types=allowed_types,
        default_allowed_types=default_allowed_types,
        pad_links=[pl.get_id() for pl in p._pad_links],
    )


def node_editor_rep(n: node.Node) -> "NodeEditorRepresentation":
    pads = [pad_editor_rep(p) for p in n.pads]
    return NodeEditorRepresentation(
        id=n.id,
        type=n.get_type(),
        editor_name=n.editor_name,
        editor_position=n.editor_position,
        editor_dimensions=n.editor_dimensions,
        pads=pads,
        description=n.get_description(),
        metadata=n.get_metadata(),
        notes=n.get_notes(),
    )
