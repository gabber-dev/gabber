# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from typing import cast

from core import pad, runtime_types
from core.node import Node, NodeMetadata
from core.pad import PropertySinkPad, StatelessSinkPad, StatelessSourcePad, types


class CreateContextMessage(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Creates new context messages with specified role and content"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="ai", secondary="llm", tags=["context", "message"])

    def resolve_pads(self):
        sink_default: list[pad.types.BasePadType] | None = [
            types.AudioClip(),
            types.VideoClip(),
            types.AVClip(),
            types.String(),
            types.Video(),
            types.TextStream(),
        ]
        role = cast(PropertySinkPad, self.get_pad("role"))
        if not role:
            role = PropertySinkPad(
                id="role",
                group="role",
                owner_node=self,
                default_type_constraints=[types.ContextMessageRole()],
                value=runtime_types.ContextMessageRole.SYSTEM,
            )
            self.pads.append(role)

        content_sink = cast(StatelessSinkPad, self.get_pad("content"))
        if not content_sink:
            content_sink = StatelessSinkPad(
                id="content",
                group="content",
                owner_node=self,
                default_type_constraints=sink_default,
            )
            self.pads.append(content_sink)

        message_source = cast(StatelessSourcePad, self.get_pad("context_message"))
        if not message_source:
            message_source = StatelessSourcePad(
                id="context_message",
                group="context_message",
                owner_node=self,
                default_type_constraints=[types.ContextMessage()],
            )
            self.pads.append(message_source)

    async def run(self):
        content_sink = cast(StatelessSinkPad, self.get_pad_required("content"))
        role_pad = cast(PropertySinkPad, self.get_pad_required("role"))
        message_source = cast(
            StatelessSourcePad, self.get_pad_required("context_message")
        )
        async for item in content_sink:
            role = role_pad.get_value()
            content: list[runtime_types.ContextMessageContentItem] = []
            if isinstance(item.value, runtime_types.AudioClip):
                content.append(
                    runtime_types.ContextMessageContentItem_Audio(clip=item.value)
                )
            elif isinstance(item.value, runtime_types.VideoClip):
                content.append(
                    runtime_types.ContextMessageContentItem_Video(clip=item.value)
                )
            elif isinstance(item.value, runtime_types.AVClip):
                content.append(
                    runtime_types.ContextMessageContentItem_Audio(clip=item.value.audio)
                )
                content.append(
                    runtime_types.ContextMessageContentItem_Video(clip=item.value.video)
                )
            elif isinstance(item.value, runtime_types.VideoFrame):
                content.append(
                    runtime_types.ContextMessageContentItem_Image(frame=item.value)
                )
            elif isinstance(item.value, str):
                content.append(
                    runtime_types.ContextMessageContentItem_Text(content=item.value)
                )
            elif isinstance(item.value, runtime_types.TextStream):
                acc = ""
                async for chunk in item.value:
                    acc += chunk
                content.append(
                    runtime_types.ContextMessageContentItem_Text(content=acc)
                )

            if len(content) > 0:
                message = runtime_types.ContextMessage(
                    role=role, content=content, tool_calls=[]
                )
                message_source.push_item(message, item.ctx)

            item.ctx.complete()
