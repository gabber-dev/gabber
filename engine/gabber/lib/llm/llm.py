# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import base64
import time
import io
import json
import logging
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, cast

from openai.types import chat

from gabber.core.runtime_types import (
    ContextMessage,
    ContextMessageContent_ChoiceDelta,
    ContextMessageContentItem_Audio,
    ContextMessageContentItem_Image,
    ContextMessageContentItem_Text,
    ContextMessageContentItem_Video,
    ContextMessageRole,
    ToolDefinition,
    Schema,
)
from gabber.lib.video.mp4_encoder import MP4_Encoder
from .token_estimator import TokenEstimator


class BaseLLM(ABC):
    @abstractmethod
    def create_generation(self, request: "LLMRequest") -> "AsyncLLMResponseHandle":
        raise NotImplementedError("Subclasses must implement create_generation method")


@dataclass
class LLMRequest:
    context: list[ContextMessage]
    tool_definitions: list[ToolDefinition]

    def estimate_tokens(self, token_estimator: TokenEstimator) -> int:
        total = 0
        for msg in self.context:
            for cnt in msg.content:
                total += token_estimator.estimate_tokens_for_content_item(cnt)

        for tool in self.tool_definitions:
            txt = tool.description
            if tool.parameters is not None:
                for k, v in tool.parameters.to_json_schema().items():
                    txt += f"{k}: {v}\n"

            total += token_estimator.estimate_tokens_for_content_item(
                ContextMessageContentItem_Text(content=txt)
            )
        return total

    async def to_openai_completion_input(
        self,
        *,
        audio_support: bool,
        video_support: bool,
    ) -> list[chat.ChatCompletionMessageParam]:
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
            new_msg: Any = {
                "role": role,
                "content": [],
            }
            for cnt in msg.content:
                if isinstance(cnt, ContextMessageContentItem_Audio):
                    if audio_support:
                        wav_buffer = io.BytesIO()
                        with wave.open(wav_buffer, "wb") as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(24000)
                            wav_file.writeframes(cnt.clip.concatted_24000hz)

                        wav_bytes = wav_buffer.getvalue()
                        base64_audio = base64.b64encode(wav_bytes).decode("utf-8")
                        new_msg["content"].append(
                            cast(
                                Any,
                                {
                                    "type": "input_audio",
                                    "input_audio": {
                                        "data": base64_audio,
                                        "format": "wav",
                                    },
                                },
                            )
                        )
                    else:
                        if not cnt.clip.transcription:
                            logging.warning(
                                "Audio content is not supported in OpenAI compatible LLMs and no transcription to fall back on."
                            )
                        new_cnt = {
                            "type": "text",
                            "text": cnt.clip.transcription,
                        }
                        new_msg["content"].append(new_cnt)
                elif isinstance(cnt, ContextMessageContentItem_Video):
                    # Less than 8 frames, send as images. Certain llm servers don't do well with small number of frames
                    if video_support and len(cnt.clip.video) > 8:
                        if not cnt.clip.mp4_bytes:
                            encoder = MP4_Encoder()
                            encoder.push_frames(cnt.clip.video)
                            cnt.clip.mp4_bytes = await encoder.eos()

                        b64_video = base64.b64encode(cnt.clip.mp4_bytes).decode("utf-8")

                        video_cnt: dict[str, Any] = {
                            "type": "video_url",
                            "video_url": {
                                "url": f"data:video/mp4;base64,{b64_video}",
                                "video_metadata": {
                                    "fps": cnt.clip.estimated_fps,
                                    "total_num_frames": len(cnt.clip.video),
                                },
                            },
                        }
                        new_msg["content"].append(cast(Any, video_cnt))
                    else:
                        for frame in cnt.clip.video:
                            oai_cnt: chat.ChatCompletionContentPartImageParam = {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{frame.to_base64_png()}"
                                },
                            }
                            new_msg["content"].append(oai_cnt)
                elif isinstance(cnt, ContextMessageContentItem_Image):
                    oai_cnt: chat.ChatCompletionContentPartImageParam = {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{cnt.frame.to_base64_png()}"
                        },
                    }
                    new_msg["content"].append(oai_cnt)
                elif isinstance(cnt, ContextMessageContentItem_Text):
                    new_cnt = {
                        "type": "text",
                        "text": cnt.content,
                    }
                    new_msg["content"].append(new_cnt)
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
            elif isinstance(tool.parameters, dict):
                parameters = tool.parameters
            elif isinstance(tool.parameters, Schema):
                parameters = tool.parameters.to_json_schema()
            else:
                parameters = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }

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


class AsyncLLMResponseHandle:
    def __init__(
        self, *, first_token_timeout: float = 45.0, total_timeout: float = 90.0
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
