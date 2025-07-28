# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

import aiohttp
from core import node, pad, runtime_types


class VLM(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Vision Language Model for processing images and text"

    @classmethod
    def get_metadata(cls) -> node.NodeMetadata:
        return node.NodeMetadata(
            primary="ai", secondary="vlm", tags=["vision", "image", "text"]
        )

    async def resolve_pads(self):
        allow_nsfw = cast(pad.PropertySinkPad, self.get_pad("allow_nsfw"))
        if not allow_nsfw:
            allow_nsfw = pad.PropertySinkPad(
                id="allow_nsfw",
                group="allow_nsfw",
                owner_node=self,
                type_constraints=[pad.types.Boolean()],
                value=False,
            )
            self.pads.append(allow_nsfw)

        allow_race_gender = cast(pad.PropertySinkPad, self.get_pad("allow_race_gender"))
        if not allow_race_gender:
            allow_race_gender = pad.PropertySinkPad(
                id="allow_race_gender",
                group="allow_race_gender",
                owner_node=self,
                type_constraints=[pad.types.Boolean()],
                value=False,
            )
            self.pads.append(allow_race_gender)

        mention_by_name = cast(pad.PropertySinkPad, self.get_pad("mention_by_name"))
        if not mention_by_name:
            mention_by_name = pad.PropertySinkPad(
                id="mention_by_name",
                group="mention_by_name",
                owner_node=self,
                type_constraints=[pad.types.String()],
                value="",
            )
            self.pads.append(mention_by_name)

        caption_source = cast(pad.StatelessSourcePad, self.get_pad("caption"))
        if not caption_source:
            caption_source = pad.StatelessSourcePad(
                id="caption",
                group="caption",
                owner_node=self,
                type_constraints=[pad.types.String()],
            )
            self.pads.append(caption_source)

        process_image = cast(pad.StatelessSinkPad, self.get_pad("process_image"))
        if not process_image:
            process_image = pad.StatelessSinkPad(
                id="process_image",
                group="process_image",
                owner_node=self,
                type_constraints=[pad.types.Video()],
            )
            self.pads.append(process_image)

    async def run(self):
        allow_nsfw = cast(pad.PropertySinkPad, self.get_pad_required("allow_nsfw"))
        allow_race_gender = cast(
            pad.PropertySinkPad, self.get_pad_required("allow_race_gender")
        )
        mention_by_name = cast(
            pad.PropertySinkPad, self.get_pad_required("mention_by_name")
        )
        caption_source = cast(pad.StatelessSourcePad, self.get_pad_required("caption"))
        process_image = cast(
            pad.StatelessSinkPad, self.get_pad_required("process_image")
        )
        running_task: asyncio.Task | None = None

        async def generation_task(
            image: runtime_types.VideoFrame, ctx: pad.RequestContext
        ):
            prompt = 'Write a short descriptive caption for this image. Your response will be used by a text-to-image model, so avoid useless meta phrases like “This image shows…”, "You are looking at...", etc.'
            if not allow_nsfw.get_value():
                prompt += " Do NOT include anything sexual; keep it PG."
            if not allow_race_gender.get_value():
                prompt += " Do NOT include information about people/characters that cannot be changed (like ethnicity, gender, etc.) but do still include changeable attributes (like hair style)."

            if mention_by_name.get_value() != "":
                prompt += f" If there is a person/character in the image, you must refer to them as {mention_by_name.get_value()}"
            image = cast(runtime_types.VideoFrame, image)
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful image captioner.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image.to_base64_png()}"
                            },
                        },
                    ],
                },
            ]
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:7002/v1/chat/completions",
                    json={"model": "", "messages": messages, "max_tokens": 500},
                    headers={"Content-Type": "application/json"},
                ) as response:
                    result = await response.json()
                    caption = (
                        result.get("choices", [])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    caption_source.push_item(caption, ctx)
                    ctx.complete()

        async for image in process_image:
            if running_task and not running_task.done():
                logging.warning(
                    "Previous LLM generation task is still running, skipping this image."
                )
                image.ctx.complete()
                continue
            try:
                running_task = asyncio.create_task(
                    generation_task(image.value, image.ctx)
                )
            except Exception as e:
                logging.error(f"Failed to start LLM generation: {e}", exc_info=e)
