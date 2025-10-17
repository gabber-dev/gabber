# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

from gabber.core.types import runtime, pad_constraints
from gabber.core.node import Node, NodeMetadata
from gabber.core.pad import PropertySinkPad, PropertySourcePad


class ContextMessage(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Stores and manages conversation context messages"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="ai", secondary="llm", tags=["context", "message"])

    def resolve_pads(self):
        role = cast(PropertySinkPad, self.get_pad("role"))
        if not role:
            role = PropertySinkPad(
                id="role",
                group="role",
                owner_node=self,
                default_type_constraints=[pad_constraints.ContextMessageRole()],
                value=runtime.ContextMessageRole(
                    value=runtime.ContextMessageRoleEnum.SYSTEM
                ),
            )

        content_sink = cast(PropertySinkPad, self.get_pad("content"))
        if not content_sink:
            content_sink = PropertySinkPad(
                id="content",
                group="content",
                owner_node=self,
                default_type_constraints=[pad_constraints.String()],
                value="You are a helpful assistant.",
            )

        message_source = cast(PropertySourcePad, self.get_pad("context_message"))
        if not message_source:
            content_sink_value = content_sink.get_value()
            assert isinstance(content_sink_value, str)
            message_source = PropertySourcePad(
                id="context_message",
                group="context_message",
                owner_node=self,
                default_type_constraints=[pad_constraints.ContextMessage()],
                value=runtime.ContextMessage(
                    role=runtime.ContextMessageRoleEnum.SYSTEM,
                    content=[
                        runtime.ContextMessageContentItem_Text(
                            content=content_sink_value
                        )
                    ],
                    tool_calls=[],
                ),
            )

        role_value = role.get_value()
        assert isinstance(role_value, runtime.ContextMessageRole)
        content_sink_value = content_sink.get_value()
        assert isinstance(content_sink_value, str)
        message_source.set_value(
            runtime.ContextMessage(
                role=role_value.value,
                content=[
                    runtime.ContextMessageContentItem_Text(content=content_sink_value)
                ],
                tool_calls=[],
            )
        )

        self.pads = [
            role,
            content_sink,
            message_source,
        ]

    async def run(self):
        content_sink = cast(PropertySinkPad, self.get_pad_required("content"))
        role_pad = cast(PropertySinkPad, self.get_pad_required("role"))
        message_source = cast(
            PropertySourcePad, self.get_pad_required("context_message")
        )

        async def content_sink_task():
            """Task to handle content from the content sink."""
            async for item in content_sink:
                role = role_pad.get_value()
                value = item.value
                assert isinstance(value, str)
                assert isinstance(role, runtime.ContextMessageRole)
                content: list[runtime.ContextMessageContentItem] = [
                    runtime.ContextMessageContentItem_Text(content=value)
                ]
                message_source.push_item(
                    runtime.ContextMessage(
                        role=role.value, content=content, tool_calls=[]
                    ),
                    item.ctx,
                )

        async def role_sink_task():
            """Task to handle role changes."""
            async for item in role_pad:
                assert isinstance(item.value, runtime.ContextMessageRole)
                message = message_source.get_value()
                assert isinstance(message, runtime.ContextMessage)
                message.role = item.value.value

        await asyncio.gather(
            content_sink_task(),
            role_sink_task(),
        )
