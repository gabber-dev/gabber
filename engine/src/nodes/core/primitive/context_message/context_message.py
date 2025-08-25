# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

from core import runtime_types
from core.node import Node, NodeMetadata
from core.pad import (
    PropertySinkPad,
    PropertySourcePad,
    types,
)


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
                default_type_constraints=[types.ContextMessageRole()],
                value=runtime_types.ContextMessageRole.SYSTEM,
            )

        content_sink = cast(PropertySinkPad, self.get_pad("content"))
        if not content_sink:
            content_sink = PropertySinkPad(
                id="content",
                group="content",
                owner_node=self,
                default_type_constraints=[types.String()],
                value="You are a helpful assistant.",
            )

        message_source = cast(PropertySourcePad, self.get_pad("context_message"))
        if not message_source:
            message_source = PropertySourcePad(
                id="context_message",
                group="context_message",
                owner_node=self,
                default_type_constraints=[types.ContextMessage()],
                value=runtime_types.ContextMessage(
                    role=runtime_types.ContextMessageRole.SYSTEM,
                    content=[
                        runtime_types.ContextMessageContentItem_Text(
                            content=content_sink.get_value()
                        )
                    ],
                    tool_calls=[],
                ),
            )

        self.pads = [
            role,
            content_sink,
            message_source,
        ]

        val = content_sink.get_value()
        if val is None:
            val = ""
        message_source.set_value(
            runtime_types.ContextMessage(
                role=runtime_types.ContextMessageRole.SYSTEM,
                content=[runtime_types.ContextMessageContentItem_Text(content=val)],
                tool_calls=[],
            )
        )

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
                content: list[runtime_types.ContextMessageContentItem] = [
                    runtime_types.ContextMessageContentItem_Text(content=item.value)
                ]
                message_source.push_item(
                    runtime_types.ContextMessage(
                        role=role, content=content, tool_calls=[]
                    ),
                    item.ctx,
                )

        async def role_sink_task():
            """Task to handle role changes."""
            async for item in role_pad:
                if isinstance(item, runtime_types.ContextMessageRole):
                    # Update the role in the last message
                    last_message = message_source.get_value()[-1]
                    last_message.role = item.value
                    message_source.push_item(last_message, item.ctx)

        await asyncio.gather(
            content_sink_task(),
            role_sink_task(),
        )
