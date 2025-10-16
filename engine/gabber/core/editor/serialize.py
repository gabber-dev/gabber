# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import Any, cast

from .. import node, pad
from ..types import pad_constraints, mapper

from .models import NodeEditorRepresentation, PadEditorRepresentation, PadReference


def pad_editor_rep(p: pad.Pad):
    value: Any | None = None
    if isinstance(p, pad.PropertyPad):
        value = mapper.Mapper.runtime_to_client(p.get_value())
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
