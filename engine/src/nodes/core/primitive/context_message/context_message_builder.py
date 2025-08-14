# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import cast

from core import pad, runtime_types
from core.node import Node, NodeMetadata
from core.pad import PropertySinkPad, StatelessSinkPad, StatelessSourcePad, types


class ContextMessageBuilder(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Creates new context messages with specified role and content"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="ai", secondary="llm", tags=["context", "message"])

    async def resolve_pads(self):
        role = cast(PropertySinkPad, self.get_pad("role"))
        if not role:
            role = PropertySinkPad(
                id="role",
                group="role",
                owner_node=self,
                type_constraints=[types.ContextMessageRole()],
                value=runtime_types.ContextMessageRole.SYSTEM,
            )
            self.pads.append(role)

        commit = cast(StatelessSinkPad, self.get_pad("commit"))
        if not commit:
            commit = StatelessSinkPad(
                id="commit",
                group="commit",
                owner_node=self,
                type_constraints=[types.Trigger()],
            )
            self.pads.append(commit)

        message_source = cast(StatelessSourcePad, self.get_pad("context_message"))
        if not message_source:
            message_source = StatelessSourcePad(
                id="context_message",
                group="context_message",
                owner_node=self,
                type_constraints=[types.ContextMessage()],
            )
            self.pads.append(message_source)

        self._resolve_content_pads()

    def _resolve_content_pads(self):
        sink_default: list[pad.types.BasePadType] | None = [
            types.AudioClip(),
            types.VideoClip(),
            types.AVClip(),
            types.String(),
            types.Video(),
        ]
        content_pads = cast(
            list[pad.StatelessSinkPad],
            [p for p in self.pads if p.get_group() == "content"],
        )
        needs_new = True
        for content_pad in content_pads:
            if content_pad.get_previous_pad() is None:
                needs_new = False

        if needs_new:
            content_sink = StatelessSinkPad(
                id=f"content_{len(content_pads)}",
                group="content",
                owner_node=self,
                type_constraints=sink_default,
            )
            self.pads.append(content_sink)

        for content_pad in content_pads:
            prev_pad = content_pad.get_previous_pad()
            if prev_pad:
                tcs = pad.types.INTERSECTION(
                    prev_pad.get_type_constraints(), sink_default
                )
                content_pad.set_type_constraints(tcs)
            else:
                content_pad.set_type_constraints(sink_default)

    async def run(self):
        content_sink = cast(StatelessSinkPad, self.get_pad_required("content"))
        role_pad = cast(PropertySinkPad, self.get_pad_required("role"))
        message_source = cast(
            StatelessSourcePad, self.get_pad_required("context_message")
        )
