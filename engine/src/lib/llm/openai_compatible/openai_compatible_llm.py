# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast

import openai
from core.runtime_types import (
    ContextMessageContent_ChoiceDelta,
    ContextMessageContent_ToolCallDelta,
)

from ..llm import AsyncLLMResponseHandle, LLMRequest


class OpenAICompatibleLLMError(Exception):
    code: int | None
    msg: str

    def __init__(self, code: int | None, msg: str):
        super().__init__(msg)
        self.code = code
        self.msg = msg


class OpenAICompatibleLLM:
    def __init__(
        self, *, headers: dict[str, str], api_key: str, base_url: str, model: str
    ):
        self._model = model
        self._client = openai.AsyncClient(
            api_key=api_key,
            default_headers=headers,
            base_url=base_url,
        )
        self._tasks = set[asyncio.Task]()

    async def create_completion(
        self,
        *,
        request: LLMRequest,
        audio_support: bool,
        video_support: bool,
        max_completion_tokens: int | None = None,
    ) -> AsyncLLMResponseHandle:
        messages = await request.to_openai_completion_input(
            audio_support=audio_support, video_support=video_support
        )
        tools = request.to_openai_completion_tools_input()

        try:
            res = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                stream=True,
                max_completion_tokens=max_completion_tokens,
            )
        except openai.APIStatusError as e:
            raise OpenAICompatibleLLMError(code=e.status_code, msg=e.message) from e

        handle = AsyncLLMResponseHandle()

        async def res_task():
            async for chunk in res:
                if len(chunk.choices) == 0:
                    continue

                choice = chunk.choices[0]
                delta = choice.delta
                if delta:
                    content = chunk.choices[0].delta.content
                    role = cast(Any, delta.role)
                    content = content if content else None
                    refusal = delta.refusal
                    tool_calls: list[ContextMessageContent_ToolCallDelta] | None = None
                    if delta.tool_calls:
                        tool_calls = [
                            ContextMessageContent_ToolCallDelta(
                                index=t.index,
                                id=t.id,
                                name=t.function.name if t.function else None,
                                arguments=t.function.arguments
                                if t.function and t.function.arguments
                                else None,
                            )
                            for t in delta.tool_calls
                        ]
                    handle.put_not_thread_safe(
                        ContextMessageContent_ChoiceDelta(
                            content=content,
                            role=role,
                            refusal=refusal,
                            tool_calls=tool_calls,
                        )
                    )

            handle.put_not_thread_safe(None)

        t = asyncio.create_task(res_task())
        t.add_done_callback(lambda _: handle.put_thread_safe(None))

        return handle
