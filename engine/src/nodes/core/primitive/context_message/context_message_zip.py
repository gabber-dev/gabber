# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
import asyncio
from typing import cast

from core import pad, runtime_types
from core.node import Node, NodeMetadata
from core.pad import PropertySinkPad, StatelessSinkPad, StatelessSourcePad, types


class ContextMessageZip(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Creates new context messages with specified role and content"

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

        message_source = cast(StatelessSourcePad, self.get_pad("context_message"))
        if not message_source:
            message_source = StatelessSourcePad(
                id="context_message",
                group="context_message",
                owner_node=self,
                default_type_constraints=[types.ContextMessage()],
            )

        num_content_pads = self.get_pad("num_contents")
        if not num_content_pads:
            num_content_pads = PropertySinkPad(
                id="num_contents",
                group="config",
                owner_node=self,
                default_type_constraints=[types.Integer()],
                value=1,
            )

        existing_content_pads = [
            p
            for p in self.pads
            if isinstance(p, StatelessSinkPad) and p.get_group() == "content"
        ]
        self.pads = [role, message_source, num_content_pads] + existing_content_pads

        content_pads = self._resolve_content_pads()
        self.pads = [role, message_source, num_content_pads] + content_pads

    def _resolve_content_pads(self):
        sink_default: list[pad.types.BasePadType] | None = [
            types.AudioClip(),
            types.VideoClip(),
            types.AVClip(),
            types.String(),
            types.Video(),
            types.TextStream(),
        ]
        num_content_pads = (
            cast(PropertySinkPad, self.get_pad_required("num_contents")).get_value()
            or 1
        )
        content_pads: list[pad.Pad] = []
        for i in range(num_content_pads):
            pad_id = f"content_{i}"
            content_pad = self.get_pad(pad_id)
            if not content_pad:
                logging.info(f"NEIL Creating content pad {pad_id}")
                content_pad = StatelessSinkPad(
                    id=pad_id,
                    group="content",
                    owner_node=self,
                    default_type_constraints=sink_default,
                )
            content_pads.append(content_pad)

        return content_pads

    async def run(self):
        role_pad = cast(PropertySinkPad, self.get_pad_required("role"))
        message_source = cast(
            StatelessSourcePad, self.get_pad_required("context_message")
        )

        contents: list[pad.StatelessSinkPad] = []
        connected_content_pads: list[pad.StatelessSinkPad] = []
        for p in self.pads:
            if isinstance(p, StatelessSinkPad) and p.get_group() == "content":
                contents.append(p)
                if p.get_previous_pad():
                    connected_content_pads.append(p)

        while True:
            try:
                items = await asyncio.gather(
                    *[anext(p) for p in connected_content_pads]
                )
                role = role_pad.get_value()
                content: list[runtime_types.ContextMessageContentItem] = []
                for item in items:
                    if isinstance(item.value, runtime_types.AudioClip):
                        content.append(
                            runtime_types.ContextMessageContentItem_Audio(
                                clip=item.value
                            )
                        )
                    elif isinstance(item.value, runtime_types.VideoClip):
                        content.append(
                            runtime_types.ContextMessageContentItem_Video(
                                clip=item.value
                            )
                        )
                    elif isinstance(item.value, runtime_types.AVClip):
                        content.append(
                            runtime_types.ContextMessageContentItem_Audio(
                                clip=item.value.audio
                            )
                        )
                        content.append(
                            runtime_types.ContextMessageContentItem_Video(
                                clip=item.value.video
                            )
                        )
                    elif isinstance(item.value, runtime_types.VideoFrame):
                        content.append(
                            runtime_types.ContextMessageContentItem_Image(
                                frame=item.value
                            )
                        )
                    elif isinstance(item.value, str):
                        content.append(
                            runtime_types.ContextMessageContentItem_Text(
                                content=item.value
                            )
                        )
                    elif isinstance(item.value, runtime_types.TextStream):
                        acc = ""
                        async for chunk in item.value:
                            acc += chunk
                        content.append(
                            runtime_types.ContextMessageContentItem_Text(content=acc)
                        )

                message = runtime_types.ContextMessage(
                    role=role, content=content, tool_calls=[]
                )

                # TODO: propagate context properly
                message_source.push_item(message, pad.RequestContext(parent=None))

                for item in items:
                    item.ctx.complete()
            except StopAsyncIteration:
                break
            except Exception as e:
                logging.error("Error while processing context message", exc_info=e)
