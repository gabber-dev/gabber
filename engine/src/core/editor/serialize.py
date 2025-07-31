# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import Any

from pydantic import BaseModel

from core import node, pad, runtime_types

from .models import (
    NodeEditorRepresentation, 
    PadEditorRepresentation, 
    PadReference,
    DisplayState,
    ConsolidatedPadRepresentation,
)


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
    nodes: list[node.Node],
    p: pad.Pad,
    v: Any | None,
):
    type_constraints = p.get_type_constraints()
    if v is not None and (type_constraints is None or len(type_constraints) != 1):
        raise ValueError(
            f"Expected exactly one type constraint for deserialization, got {type_constraints}, value: {v}, pad: {p.get_id()}"
        )
    if type_constraints is None:
        return None
    tc = type_constraints[0]

    if not isinstance(p, pad.PropertyPad):
        logging.error(f"Expected PropertyPad instance, got {type(p)}")
        return None

    if isinstance(tc, pad.types.NodeReference):
        if isinstance(p, pad.ProxyPad):
            other = p.get_other()
            if not isinstance(other, pad.PropertyPad):
                logging.error(f"Expected PropertyPad for other pad, got {type(other)}")
                return None
            return other.get_value()
        else:
            if not isinstance(v, str):
                return None
            for node in nodes:
                if node.id == v:
                    return node
            raise ValueError(
                f"Node with id {v} not found in nodes list. Available nodes: {[n.id for n in nodes]}"
            )

    if isinstance(v, str | float | int):
        return v
    elif isinstance(v, BaseModel):
        return v
    elif isinstance(v, dict):
        if isinstance(tc, pad.types.ContextMessage):
            return runtime_types.ContextMessage.model_validate(v)
        elif isinstance(tc, pad.types.Object):
            return v
        elif isinstance(tc, pad.types.Schema):
            return runtime_types.Schema.model_validate(v)
        elif isinstance(tc, pad.types.BoundingBox):
            return runtime_types.BoundingBox.model_validate(v)
        elif isinstance(tc, pad.types.Point):
            return runtime_types.Point.model_validate(v)
    elif isinstance(v, list):
        if not isinstance(tc, pad.types.List):
            logging.error(
                f"Expected List type constraint for list deserialization, got {type(tc)}"
            )
            return None
        list_types = tc.item_type_constraints
        if not list_types or len(list_types) != 1:
            logging.error(
                f"List type constraints: {list_types}, value: {v}, type_constraints: {type_constraints}"
            )
            return None

        items = [deserialize_pad_value(nodes, p, item) for item in v]
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
    return PadEditorRepresentation(
        id=p.get_id(),
        group=p.get_group(),
        type=p.get_editor_type(),
        value=value,
        next_pads=next_pads,
        previous_pad=previous_pad,
        allowed_types=p.get_type_constraints(),
    )


def node_editor_rep(n: node.Node) -> "NodeEditorRepresentation":
    pads = [pad_editor_rep(p) for p in n.pads]
    
    # Create consolidated pads when node is minimized
    consolidated_pads = []
    if n.display_state == "minimized":
        pad_groups = n.get_consolidated_pads()
        if pad_groups["sink"]:
            consolidated_pads.append(ConsolidatedPadRepresentation(
                id=f"{n.id}-consolidated-sink",
                type="sink",
                represented_pads=pad_groups["sink"]
            ))
        if pad_groups["source"]:
            consolidated_pads.append(ConsolidatedPadRepresentation(
                id=f"{n.id}-consolidated-source", 
                type="source",
                represented_pads=pad_groups["source"]
            ))
    
    return NodeEditorRepresentation(
        id=n.id,
        type=n.get_type(),
        editor_name=n.editor_name,
        editor_position=n.editor_position,
        editor_dimensions=n.editor_dimensions,
        pads=pads,
        description=n.get_description(),
        metadata=n.get_metadata(),
        display_state=DisplayState(n.display_state),
        consolidated_pads=consolidated_pads,
    )
