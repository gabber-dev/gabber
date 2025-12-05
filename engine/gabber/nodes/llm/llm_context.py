# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from gabber.core import node, pad
from gabber.core.types import runtime
from gabber.core.types import pad_constraints

DEFAULT_SYSTEM_MESSAGE = runtime.ContextMessage(
    role=runtime.ContextMessageRoleEnum.SYSTEM,
    content=[
        runtime.ContextMessageContentItem_Text(content="You are a helpful assistant.")
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

    def resolve_pads(self):
        num_inserts = cast(pad.PropertySinkPad, self.get_pad("num_inserts"))
        if not num_inserts:
            num_inserts = pad.PropertySinkPad(
                id="num_inserts",
                group="config",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer(minimum=1)],
                value=1,
            )

        new_user_message = cast(
            pad.StatelessSourcePad, self.get_pad("new_user_message")
        )
        if not new_user_message:
            new_user_message = pad.StatelessSourcePad(
                id="new_user_message",
                group="new_user_message",
                owner_node=self,
                default_type_constraints=[pad_constraints.ContextMessage()],
            )
        max_non_system_messages = cast(
            pad.PropertySinkPad, self.get_pad("max_non_system_messages")
        )
        if not max_non_system_messages:
            max_non_system_messages = pad.PropertySinkPad(
                id="max_non_system_messages",
                group="max_non_system_messages",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer(minimum=0)],
                value=64,
            )

        max_videos = cast(pad.PropertySinkPad, self.get_pad("max_videos"))
        if not max_videos:
            max_videos = pad.PropertySinkPad(
                id="max_videos",
                group="max_videos",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer(minimum=0)],
                value=2,
            )

        max_audios = cast(pad.PropertySinkPad, self.get_pad("max_audios"))
        if not max_audios:
            max_audios = pad.PropertySinkPad(
                id="max_audios",
                group="max_audios",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer(minimum=0)],
                value=2,
            )

        max_images = cast(pad.PropertySinkPad, self.get_pad("max_images"))
        if not max_images:
            max_images = pad.PropertySinkPad(
                id="max_images",
                group="max_images",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer(minimum=0)],
                value=2,
            )

        system_message = cast(pad.PropertySinkPad, self.get_pad("system_message"))
        if not system_message:
            system_message = pad.PropertySinkPad(
                id="system_message",
                group="system_message",
                owner_node=self,
                default_type_constraints=[pad_constraints.ContextMessage()],
                value=DEFAULT_SYSTEM_MESSAGE,
            )

        source = cast(pad.PropertySourcePad, self.get_pad("source"))
        if not source:
            source = pad.PropertySourcePad(
                id="source",
                group="source",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.List(
                        item_type_constraints=[pad_constraints.ContextMessage()]
                    )
                ],
                value=[system_message.get_value()],
            )

        source._set_value([system_message.get_value()])

        insert_pads: list[pad.Pad] = []
        num_inserts_value = num_inserts.get_value() or 1
        assert isinstance(num_inserts_value, int)

        for i in range(num_inserts_value):
            pad_id = f"insert_{i}"
            insert_pad = self.get_pad(pad_id)
            if not insert_pad:
                insert_pad = pad.StatelessSinkPad(
                    id=pad_id,
                    group="insert",
                    owner_node=self,
                    default_type_constraints=[pad_constraints.ContextMessage()],
                )
            insert_pads.append(insert_pad)

        for p in self.pads:
            if p.get_group() == "insert":
                if p not in insert_pads:
                    self.pads.remove(p)

        self.pads = (
            [
                num_inserts,
                max_non_system_messages,
                max_videos,
                max_audios,
                max_images,
                system_message,
            ]
            + insert_pads
            + [source, new_user_message]
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

        def prune(msgs: list[runtime.ContextMessage]):
            system_message_value = system_message.get_value()
            max_non_system_messages_value = max_non_system_messages.get_value()
            assert isinstance(max_non_system_messages_value, int)
            assert isinstance(system_message_value, runtime.ContextMessage)
            new_values: list[runtime.ContextMessage] = [system_message_value]
            non_system_messages: list[runtime.ContextMessage] = []
            for item in msgs:
                if item.role != runtime.ContextMessageRoleEnum.SYSTEM:
                    non_system_messages.append(item)

            pruned = non_system_messages[-max_non_system_messages_value:]

            tool_call_ids = set()
            for msg in pruned:
                if (
                    msg.role == runtime.ContextMessageRoleEnum.ASSISTANT
                    and msg.tool_calls
                ):
                    for tool_call in msg.tool_calls:
                        tool_call_ids.add(tool_call.call_id)

            final_pruned: list[runtime.ContextMessage] = []
            for msg in pruned:
                if msg.role == runtime.ContextMessageRoleEnum.TOOL:
                    if msg.tool_call_id in tool_call_ids:
                        final_pruned.append(msg)
                else:
                    final_pruned.append(msg)

            audio_count = 0
            video_count = 0
            image_count = 0
            for msg in final_pruned[::-1]:
                for content in msg.content:
                    if isinstance(content, runtime.ContextMessageContentItem_Audio):
                        audio_count += 1
                    elif isinstance(content, runtime.ContextMessageContentItem_Video):
                        video_count += 1
                    elif isinstance(content, runtime.ContextMessageContentItem_Image):
                        image_count += 1

                if audio_count > max_audios:
                    text_converted: list[runtime.ContextMessageContentItem] = [
                        runtime.ContextMessageContentItem_Text(
                            content=cast(
                                str,
                                cast(
                                    runtime.ContextMessageContentItem_Audio, c
                                ).clip.transcription,
                            )
                        )
                        for c in msg.content
                        if isinstance(c, runtime.ContextMessageContentItem_Audio)
                        and c.clip.transcription is not None
                    ]
                    msg.content = text_converted + [
                        c
                        for c in msg.content
                        if not isinstance(c, runtime.ContextMessageContentItem_Audio)
                    ]
                if video_count > max_videos:
                    msg.content = [
                        content
                        for content in msg.content
                        if not isinstance(
                            content, runtime.ContextMessageContentItem_Video
                        )
                    ]
                if image_count > max_images:
                    msg.content = [
                        content
                        for content in msg.content
                        if not isinstance(
                            content, runtime.ContextMessageContentItem_Image
                        )
                    ]

            final_pruned = [msg for msg in final_pruned if msg.content]

            new_values.extend(final_pruned)
            return new_values

        async def pad_task(p: pad.SinkPad):
            async for item in p:
                assert isinstance(item.value, runtime.ContextMessage)
                source_value = source.get_value()
                assert isinstance(source_value, list)
                source_value = cast(list[runtime.ContextMessage], source_value)
                new_msgs = prune(source_value + [item.value])
                if item.value.role == runtime.ContextMessageRoleEnum.USER:
                    new_user_message.push_item(item.value, item.ctx)

                source._set_value(new_msgs)
                item.ctx.complete()

        async def system_message_task():
            async for item in system_message:
                source_value = source.get_value()
                assert isinstance(source_value, list)
                source_value = cast(list[runtime.ContextMessage], source_value)
                if isinstance(item.value, runtime.ContextMessage):
                    source_value[0] = item.value
                    source._set_value(source.get_value())
                item.ctx.complete()

        for p in self.pads:
            if isinstance(p, pad.SinkPad):
                logging.info(f"LLMContext monitoring sink pad: {p.get_id()}")
                tasks.append(asyncio.create_task(pad_task(p)))

        tasks.append(asyncio.create_task(system_message_task()))
        await asyncio.gather(*tasks)
