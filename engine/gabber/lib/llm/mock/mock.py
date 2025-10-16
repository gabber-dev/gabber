# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging

from gabber.core.types import runtime

from ..llm import AsyncLLMResponseHandle, BaseLLM, LLMRequest

MOCK_RESPONSES = [
    "This is a mock response.",
    "Another mock response for testing.",
    "Mock response with no real content.",
    "Just a placeholder response. What do you think?",
    "This is a fake response to simulate LLM behavior.",
]


class MockLLM(BaseLLM):
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._idx = 0
        self._tasks: set[asyncio.Task] = set()

    def create_generation(self, request: LLMRequest) -> AsyncLLMResponseHandle:
        self._idx += 1
        if self._idx >= len(MOCK_RESPONSES):
            self._idx = 0
        handle = AsyncLLMResponseHandle()

        async def resp_task():
            try:
                resp = MOCK_RESPONSES[self._idx]
                split = resp.split(" ")
                for i in range(len(split)):
                    await asyncio.sleep(0.1)
                    handle.put_thread_safe(
                        runtime.ContextMessageContent_ChoiceDelta(
                            content=split[i] + " ",
                            tool_calls=[],
                            refusal=None,
                            role=runtime.ContextMessageRole.ASSISTANT,
                        )
                    )
            except Exception:
                logging.error("Error while processing mock response", exc_info=True)
            except asyncio.CancelledError:
                logging.info("Mock response task was cancelled")

            handle.put_thread_safe(None)

        t = asyncio.create_task(resp_task())
        self._tasks.add(t)
        t.add_done_callback(lambda _: self._tasks.discard(t))

        def on_cancel():
            t.cancel()

        handle.set_on_cancel(on_cancel)

        return handle
