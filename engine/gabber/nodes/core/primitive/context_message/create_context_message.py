# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from gabber.core.types import runtime, pad_constraints
from gabber.core.node import Node, NodeMetadata
from gabber.core.pad import PropertySinkPad, StatelessSinkPad, StatelessSourcePad


class CreateContextMessage(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Creates new context messages with specified role and content"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="ai", secondary="llm", tags=["context", "message"])

    def resolve_pads(self):
        sink_default: list[pad_constraints.BasePadType] | None = [
            pad_constraints.AudioClip(),
            pad_constraints.VideoClip(),
            pad_constraints.AVClip(),
            pad_constraints.String(),
            pad_constraints.Video(),
            pad_constraints.TextStream(),
        ]
        role = cast(PropertySinkPad, self.get_pad("role"))
        if not role:
            role = PropertySinkPad(
                id="role",
                group="role",
                owner_node=self,
                default_type_constraints=[pad_constraints.ContextMessageRole()],
                value=runtime.ContextMessageRole(
                    value=runtime.ContextMessageRoleEnum.USER
                ),
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
                default_type_constraints=[pad_constraints.ContextMessage()],
            )
            self.pads.append(message_source)

    async def run(self):
        content_sink = cast(StatelessSinkPad, self.get_pad_required("content"))
        role_pad = self.get_property_sink_pad_required(
            runtime.ContextMessageRole, "role"
        )
        message_source = cast(
            StatelessSourcePad, self.get_pad_required("context_message")
        )
        async for item in content_sink:
            role = role_pad.get_value()
            content: list[runtime.ContextMessageContentItem] = []
            if isinstance(item.value, runtime.AudioClip):
                content.append(runtime.ContextMessageContentItem_Audio(clip=item.value))
            elif isinstance(item.value, runtime.VideoClip):
                content.append(runtime.ContextMessageContentItem_Video(clip=item.value))
            elif isinstance(item.value, runtime.AVClip):
                content.append(
                    runtime.ContextMessageContentItem_Audio(clip=item.value.audio)
                )
                content.append(
                    runtime.ContextMessageContentItem_Video(clip=item.value.video)
                )
            elif isinstance(item.value, runtime.VideoFrame):
                content.append(
                    runtime.ContextMessageContentItem_Image(frame=item.value)
                )
            elif isinstance(item.value, str):
                content.append(
                    runtime.ContextMessageContentItem_Text(content=item.value)
                )
            elif isinstance(item.value, runtime.TextStream):
                acc = ""
                async for chunk in item.value:
                    acc += chunk
                content.append(runtime.ContextMessageContentItem_Text(content=acc))

            if len(content) > 0:
                message = runtime.ContextMessage(
                    role=role.value, content=content, tool_calls=[]
                )
                message_source.push_item(message, item.ctx)

            item.ctx.complete()
