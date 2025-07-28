# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, cast

from core.runtime_types import (
    ContextMessage,
    ContextMessageContent_ChoiceDelta,
    ContextMessageContentItem_Audio,
    ContextMessageContentItem_Image,
    ContextMessageContentItem_Text,
    ContextMessageContentItem_Video,
    ContextMessageRole,
    ToolDefinition,
)
from openai.types import chat


class BaseLLM(ABC):
    @abstractmethod
    def create_generation(self, request: "LLMRequest") -> "AsyncLLMResponseHandle":
        raise NotImplementedError("Subclasses must implement create_generation method")


@dataclass
class LLMRequest:
    context: list[ContextMessage]
    tool_definitions: list[ToolDefinition]

    def to_openai_completion_input(self) -> list[chat.ChatCompletionMessageParam]:
        res: list[chat.ChatCompletionMessageParam] = []
        for msg in self.context:
            role = cast(Any, msg.role.value)
            if msg.role == ContextMessageRole.TOOL:
                tool_call_id = msg.tool_call_id
                if tool_call_id is None:
                    logging.warning(
                        "Tool message without tool_call_id found in context. "
                        "This is not supported in OpenAI compatible LLMs."
                    )
                    continue

                txt_cnt = ""
                for cnt in msg.content:
                    if isinstance(cnt, ContextMessageContentItem_Text):
                        txt_cnt += cnt.content
                tool_msg: chat.ChatCompletionToolMessageParam = {
                    "role": role,
                    "content": txt_cnt,
                    "tool_call_id": msg.tool_call_id if msg.tool_call_id else "ERROR",
                }
                res.append(tool_msg)
                continue
            new_msg: chat.ChatCompletionMessageParam | None = None
            for cnt in msg.content:
                if isinstance(cnt, ContextMessageContentItem_Audio):
                    if not cnt.clip.transcription:
                        logging.warning(
                            "Audio content is not supported in OpenAI compatible LLMs and no transcription to fall back on."
                        )
                    new_msg = {
                        "role": role,
                        "content": cnt.clip.transcription,
                    }

                elif isinstance(cnt, ContextMessageContentItem_Video):
                    logging.warning(
                        "Video content is not supported in OpenAI compatible LLMs. "
                    )
                elif isinstance(cnt, ContextMessageContentItem_Image):
                    oai_cnt: chat.ChatCompletionContentPartImageParam = {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{cnt.frame.to_base64_png()}"
                        },
                    }
                    new_msg = {
                        "role": role,
                        "content": [oai_cnt],
                    }
                elif isinstance(cnt, ContextMessageContentItem_Text):
                    new_msg = {
                        "role": role,
                        "content": cnt.content,
                    }
                else:
                    raise ValueError(f"Unsupported content type: {type(cnt)}")

            if new_msg is None:
                logging.warning(
                    "Message with no content found in context. "
                    "This is not supported in OpenAI compatible LLMs."
                )
                continue

            if msg.role == ContextMessageRole.ASSISTANT:
                if msg.tool_calls:
                    tcs: list[chat.ChatCompletionMessageToolCallParam] = []
                    for call in msg.tool_calls:
                        args = json.dumps(call.arguments) if call.arguments else ""
                        tcs.append(
                            chat.ChatCompletionMessageToolCallParam(
                                id=call.call_id,
                                function=chat.chat_completion_message_tool_call_param.Function(
                                    name=call.name,
                                    arguments=args,
                                ),
                                type="function",
                            )
                        )
                    cast(chat.ChatCompletionAssistantMessageParam, new_msg)[
                        "tool_calls"
                    ] = tcs

            res.append(new_msg)

        return res

    def to_openai_completion_tools_input(self) -> list[chat.ChatCompletionToolParam]:
        tools: list[chat.ChatCompletionToolParam] = []
        for tool in self.tool_definitions:
            parameters: dict[str, Any] | None = None
            if tool.parameters is None:
                parameters = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
            else:
                parameters = tool.parameters.to_json_schema()

            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": parameters,
                    },
                }
            )
        return tools

    def _qwen_2_5_omni_vllm_prompt(self) -> str:
        prompt = ""

        for msg in self.context:
            prompt += f"<|im_start|>{msg.role}\n"

            for cnt in msg.content:
                if isinstance(cnt, ContextMessageContentItem_Audio):
                    prompt += "<|audio_bos|><|AUDIO|><|audio_eos|>\n"
                elif isinstance(cnt, ContextMessageContentItem_Video):
                    prompt += "<|vision_bos|><|VIDEO|><|vision_eos|>\n"
                elif isinstance(cnt, ContextMessageContentItem_Text):
                    text_content = cnt.content
                    prompt += f"{text_content}\n"
                else:
                    raise ValueError(f"Unsupported content type: {type(cnt)}")
            prompt += "<|im_end|>\n"

        prompt += "<|im_start|>assistant\n"
        return prompt

    def to_qwen_2_5_omni_input(self):
        input: dict = {
            "prompt": self._qwen_2_5_omni_vllm_prompt(),
        }
        audios = []
        videos = []
        for msg in self.context:
            for cnt in msg.content:
                if isinstance(cnt, ContextMessageContentItem_Audio):
                    audios.append((cnt.clip.fp32_44100, 44100))
                elif isinstance(cnt, ContextMessageContentItem_Video):
                    videos.append(cnt.clip.stacked_bgr_frames)

        if len(audios) > 0 or len(videos) > 0:
            input["multi_modal_data"] = {}

        if len(audios) > 0:
            input["multi_modal_data"]["audio"] = audios

        if len(videos) > 0:
            input["multi_modal_data"]["video"] = videos

        return input


class AsyncLLMResponseHandle:
    def __init__(
        self, *, first_token_timeout: float = 5.0, total_timeout: float = 30.0
    ):
        self._first_token_timeout = first_token_timeout
        self._total_timeout = total_timeout
        self._loop = asyncio.get_event_loop()
        self._on_cancel: Callable[[], None] | None = None
        self._output_queue = asyncio.Queue[ContextMessageContent_ChoiceDelta | None]()
        self._first_token_t = asyncio.create_task(self._first_token_timeout_task())
        self._total_timeout_t = asyncio.create_task(self._total_timeout_task())
        self._first_token_timeout_cancelled = False

    async def _first_token_timeout_task(self):
        await asyncio.sleep(self._first_token_timeout)
        logging.warning(
            f"LLM generation timed out after {self._first_token_timeout} seconds."
        )
        self.cancel()

    async def _total_timeout_task(self):
        await asyncio.sleep(self._total_timeout)
        logging.warning(
            f"LLM generation timed out after {self._total_timeout} seconds."
        )
        self.cancel()

    def set_on_cancel(self, on_cancel: Callable[[], None]):
        self._on_cancel = on_cancel

    def cancel(self):
        if self._on_cancel:
            self._on_cancel()
        self._output_queue.put_nowait(None)

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self._output_queue.get()
        if item is None:
            raise StopAsyncIteration
        return item

    def put_thread_safe(self, item: ContextMessageContent_ChoiceDelta | None):
        if not self._first_token_timeout_cancelled:
            self._first_token_timeout_cancelled = True
            self._loop.call_soon_threadsafe(self._first_token_t.cancel)

        if item is None:
            self._loop.call_soon_threadsafe(self._total_timeout_t.cancel)

        self._loop.call_soon_threadsafe(self._output_queue.put_nowait, item)

    def put_not_thread_safe(self, item: ContextMessageContent_ChoiceDelta | None):
        if not self._first_token_timeout_cancelled:
            self._first_token_timeout_cancelled = True
            self._first_token_t.cancel()

        if item is None:
            self._total_timeout_t.cancel()

        self._output_queue.put_nowait(item)
