# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from core import node, pad, runtime_types

DEFAULT_SYSTEM_MESSAGE = runtime_types.ContextMessage(
    role=runtime_types.ContextMessageRole.SYSTEM,
    content=[
        runtime_types.ContextMessageContentItem_Text(
            content="You are a helpful assistant."
        )
    ],
    tool_calls=[],
)


class LLMContext(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Manages conversation context for language models"

    @classmethod
    def get_metadata(cls) -> node.NodeMetadata:
        return node.NodeMetadata(
            primary="ai", secondary="llm", tags=["context", "memory"]
        )

    async def run(self):
        system_message = cast(
            pad.PropertySinkPad, self.get_pad_required("system_message")
        )
        max_non_system_messages = cast(
            pad.PropertySinkPad, self.get_pad_required("max_non_system_messages")
        )
        new_user_message = cast(
            pad.StatelessSourcePad, self.get_pad_required("new_user_message")
        )
        max_videos_pad = cast(
            pad.PropertySourcePad, self.get_pad_required("max_videos")
        )
        max_audios_pad = cast(
            pad.PropertySourcePad, self.get_pad_required("max_audios")
        )
        max_images_pad = cast(
            pad.PropertySourcePad, self.get_pad_required("max_images")
        )
        max_videos = cast(int, max_videos_pad.get_value())
        max_audios = cast(int, max_audios_pad.get_value())
        max_images = cast(int, max_images_pad.get_value())

        source = cast(pad.PropertySourcePad, self.get_pad_required("source"))
        tasks: list[asyncio.Task] = []

        def prune(msgs: list[runtime_types.ContextMessage]):
            new_values: list[runtime_types.ContextMessage] = [
                system_message.get_value()
            ]
            non_system_messages: list[runtime_types.ContextMessage] = []
            for item in msgs:
                if item.role != runtime_types.ContextMessageRole.SYSTEM:
                    non_system_messages.append(item)

            pruned = non_system_messages[-max_non_system_messages.get_value() :]

            tool_call_ids = set()
            for msg in pruned:
                if (
                    msg.role == runtime_types.ContextMessageRole.ASSISTANT
                    and msg.tool_calls
                ):
                    for tool_call in msg.tool_calls:
                        tool_call_ids.add(tool_call.call_id)

            final_pruned: list[runtime_types.ContextMessage] = []
            for msg in pruned:
                if msg.role == runtime_types.ContextMessageRole.TOOL:
                    if msg.tool_call_id in tool_call_ids:
                        final_pruned.append(msg)
                else:
                    final_pruned.append(msg)

            audio_count = 0
            video_count = 0
            image_count = 0
            for msg in final_pruned[::-1]:
                for content in msg.content:
                    if isinstance(
                        content, runtime_types.ContextMessageContentItem_Audio
                    ):
                        audio_count += 1
                    elif isinstance(
                        content, runtime_types.ContextMessageContentItem_Video
                    ):
                        video_count += 1
                    elif isinstance(
                        content, runtime_types.ContextMessageContentItem_Image
                    ):
                        image_count += 1

                if audio_count > max_audios:
                    text_converted: list[runtime_types.ContextMessageContentItem] = [
                        runtime_types.ContextMessageContentItem_Text(
                            content=cast(
                                str,
                                cast(
                                    runtime_types.ContextMessageContentItem_Audio, c
                                ).clip.transcription,
                            )
                        )
                        for c in msg.content
                        if isinstance(c, runtime_types.ContextMessageContentItem_Audio)
                        and c.clip.transcription is not None
                    ]
                    msg.content = text_converted + [
                        c
                        for c in msg.content
                        if not isinstance(
                            c, runtime_types.ContextMessageContentItem_Audio
                        )
                    ]
                if video_count > max_videos:
                    msg.content = [
                        content
                        for content in msg.content
                        if not isinstance(
                            content, runtime_types.ContextMessageContentItem_Video
                        )
                    ]
                if image_count > max_images:
                    msg.content = [
                        content
                        for content in msg.content
                        if not isinstance(
                            content, runtime_types.ContextMessageContentItem_Image
                        )
                    ]

            new_values.extend(final_pruned)
            return new_values

        async def pad_task(p: pad.SinkPad):
            async for item in p:
                assert isinstance(item.value, runtime_types.ContextMessage)
                new_msgs = prune(source.get_value() + [item.value])
                if item.value.role == runtime_types.ContextMessageRole.USER:
                    new_user_message.push_item(item.value, item.ctx)

                source.set_value(new_msgs)
                item.ctx.complete()

        async def system_message_task():
            async for item in system_message:
                if isinstance(item.value, runtime_types.ContextMessage):
                    source.get_value()[0] = item.value
                    source.set_value(source.get_value())
                item.ctx.complete()

        for p in self.pads:
            if isinstance(p, pad.SinkPad):
                tasks.append(asyncio.create_task(pad_task(p)))

        tasks.append(asyncio.create_task(system_message_task()))
        await asyncio.gather(*tasks)

    def resolve_pads(self):
        new_user_message = cast(
            pad.StatelessSourcePad, self.get_pad("new_user_message")
        )
        if not new_user_message:
            new_user_message = pad.StatelessSourcePad(
                id="new_user_message",
                group="new_user_message",
                owner_node=self,
                type_constraints=[pad.types.ContextMessage()],
            )
            self.pads.append(new_user_message)
        max_non_system_messages = cast(
            pad.PropertySinkPad, self.get_pad("max_non_system_messages")
        )
        if not max_non_system_messages:
            max_non_system_messages = pad.PropertySinkPad(
                id="max_non_system_messages",
                group="max_non_system_messages",
                owner_node=self,
                type_constraints=[pad.types.Integer(minimum=0)],
                value=64,
            )
            self.pads.append(max_non_system_messages)

        max_videos = cast(pad.PropertySinkPad, self.get_pad("max_videos"))
        if not max_videos:
            max_videos = pad.PropertySinkPad(
                id="max_videos",
                group="max_videos",
                owner_node=self,
                type_constraints=[pad.types.Integer(minimum=0)],
                value=2,
            )
            self.pads.append(max_videos)

        max_audios = cast(pad.PropertySinkPad, self.get_pad("max_audios"))
        if not max_audios:
            max_audios = pad.PropertySinkPad(
                id="max_audios",
                group="max_audios",
                owner_node=self,
                type_constraints=[pad.types.Integer(minimum=0)],
                value=2,
            )
            self.pads.append(max_audios)

        max_images = cast(pad.PropertySinkPad, self.get_pad("max_images"))
        if not max_images:
            max_images = pad.PropertySinkPad(
                id="max_images",
                group="max_images",
                owner_node=self,
                type_constraints=[pad.types.Integer(minimum=0)],
                value=2,
            )
            self.pads.append(max_images)

        system_message = cast(pad.PropertySinkPad, self.get_pad("system_message"))
        if not system_message:
            system_message = pad.PropertySinkPad(
                id="system_message",
                group="system_message",
                owner_node=self,
                type_constraints=[pad.types.ContextMessage()],
                value=DEFAULT_SYSTEM_MESSAGE,
            )
            self.pads.append(system_message)

        insert_sink = cast(pad.StatelessSinkPad, self.get_pad("insert_0"))
        if not insert_sink:
            insert_sink = pad.StatelessSinkPad(
                id="insert_0",
                group="insert",
                owner_node=self,
                type_constraints=[pad.types.ContextMessage()],
            )
            self.pads.append(insert_sink)

        source = cast(pad.PropertySourcePad, self.get_pad("source"))
        if not source:
            source = pad.PropertySourcePad(
                id="source",
                group="source",
                owner_node=self,
                type_constraints=[
                    pad.types.List(item_type_constraints=[pad.types.ContextMessage()])
                ],
                value=[system_message.get_value()],
            )
            self.pads.append(source)

        source.set_value([system_message.get_value()])

        connected_insert_pads = [
            p
            for p in self.pads
            if p.get_id().startswith("insert_")
            and isinstance(p, pad.SinkPad)
            and p.get_previous_pad()
        ]

        connected_insert_pads.sort(key=lambda p: int(p.get_id().split("_")[1]))

        max_index = max(
            (int(p.get_id().split("_")[1]) for p in connected_insert_pads), default=-1
        )

        new_pads = [
            source,
            system_message,
            new_user_message,
            max_non_system_messages,
            max_images,
            max_audios,
            max_videos,
        ]
        for i in range(max_index + 2):  # +2 to include next ID and one extra
            pad_id = f"insert_{i}"
            existing_pad = next((p for p in self.pads if p.get_id() == pad_id), None)
            if existing_pad and existing_pad in connected_insert_pads:
                new_pads.append(existing_pad)
            else:
                new_pads.append(
                    pad.StatelessSinkPad(
                        id=pad_id,
                        group="insert",
                        owner_node=self,
                        type_constraints=[pad.types.ContextMessage()],
                    )
                )

        self.pads = new_pads

        source.set_type_constraints(
            [pad.types.List(item_type_constraints=[pad.types.ContextMessage()])]
        )
