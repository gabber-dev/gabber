# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from core import node, pad, runtime_types
from core.node import NodeMetadata
from lib.llm import AsyncLLMResponseHandle, LLMRequest, openai_compatible
from utils import get_full_content_from_deltas


class QwenOmniLLM(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Send and receive responses from any Qwen-omni language model"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="ai", secondary="local", tags=["completion", "text", "qwen-omni"]
        )

    async def resolve_pads(self):
        run_trigger = cast(pad.StatelessSinkPad, self.get_pad("run_trigger"))
        if not run_trigger:
            run_trigger = pad.StatelessSinkPad(
                id="run_trigger",
                group="run_trigger",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(run_trigger)

        started_source = cast(pad.StatelessSourcePad, self.get_pad("started"))
        if not started_source:
            started_source = pad.StatelessSourcePad(
                id="started",
                group="started",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(started_source)

        first_token_source = cast(pad.StatelessSourcePad, self.get_pad("first_token"))
        if not first_token_source:
            first_token_source = pad.StatelessSourcePad(
                id="first_token",
                group="first_token",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(first_token_source)

        text_stream_source = cast(pad.StatelessSourcePad, self.get_pad("text_stream"))
        if not text_stream_source:
            text_stream_source = pad.StatelessSourcePad(
                id="text_stream",
                group="text_stream",
                owner_node=self,
                type_constraints=[pad.types.TextStream()],
            )
            self.pads.append(text_stream_source)

        context_message_source = cast(
            pad.StatelessSourcePad, self.get_pad("context_message")
        )
        if not context_message_source:
            context_message_source = pad.StatelessSourcePad(
                id="context_message",
                group="context_message",
                owner_node=self,
                type_constraints=[pad.types.ContextMessage()],
            )
            self.pads.append(context_message_source)

        finished_source = cast(pad.StatelessSourcePad, self.get_pad("finished"))
        if not finished_source:
            finished_source = pad.StatelessSourcePad(
                id="finished",
                group="finished",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(finished_source)

        cancel_trigger = cast(pad.StatelessSinkPad, self.get_pad("cancel_trigger"))
        if not cancel_trigger:
            cancel_trigger = pad.StatelessSinkPad(
                id="cancel_trigger",
                group="cancel_trigger",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(cancel_trigger)

        base_url_sink = cast(pad.PropertySinkPad, self.get_pad("base_url"))
        if not base_url_sink:
            base_url_sink = pad.PropertySinkPad(
                id="base_url",
                group="base_url",
                owner_node=self,
                type_constraints=[pad.types.String()],
                value="http://localhost:7002/v1",
            )
            self.pads.append(base_url_sink)

        context_sink = cast(pad.PropertySinkPad, self.get_pad("context"))
        if not context_sink:
            context_sink = pad.PropertySinkPad(
                id="context",
                group="context",
                owner_node=self,
                type_constraints=[
                    pad.types.List(item_type_constraints=[pad.types.ContextMessage()])
                ],
                value=[
                    runtime_types.ContextMessage(
                        role=runtime_types.ContextMessageRole.SYSTEM,
                        content=[
                            runtime_types.ContextMessageContentItem_Text(
                                content="You are a helpful assistant."
                            )
                        ],
                        tool_calls=[],
                    )
                ],
            )
            self.pads.append(context_sink)

    async def run(self):
        base_url_sink = cast(pad.PropertySinkPad, self.get_pad_required("base_url"))
        cancel_trigger = cast(
            pad.StatelessSinkPad, self.get_pad_required("cancel_trigger")
        )
        text_stream_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("text_stream")
        )
        started_source = cast(pad.StatelessSourcePad, self.get_pad_required("started"))
        finished_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("finished")
        )
        context_sink = cast(pad.PropertySinkPad, self.get_pad_required("context"))
        context_message_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("context_message")
        )
        run_trigger = cast(pad.StatelessSinkPad, self.get_pad_required("run_trigger"))

        self.llm = openai_compatible.OpenAICompatibleLLM(
            base_url=base_url_sink.get_value(),
            api_key="",
            headers={},
            model="",
        )

        running_handle: AsyncLLMResponseHandle | None = None
        tasks: set[asyncio.Task] = set()

        async def cancel_task():
            nonlocal running_handle
            async for item in cancel_trigger:
                logging.info("Cancelling LLM generation request.")
                if running_handle is not None:
                    running_handle.cancel()
                item.ctx.complete()

        async def generation_task(
            handle: AsyncLLMResponseHandle, ctx: pad.RequestContext
        ):
            all_deltas: list[runtime_types.ContextMessageContent_ChoiceDelta] = []
            text_stream = runtime_types.TextStream()
            text_stream_source.push_item(text_stream, ctx)
            try:
                started_source.push_item(runtime_types.Trigger(), ctx)
                async for item in handle:
                    if item.content:
                        text_stream.push_text(item.content)

                    all_deltas.append(item)

                text_stream.eos()

                full_content = get_full_content_from_deltas(all_deltas)
                context_message_source.push_item(
                    runtime_types.ContextMessage(
                        role=runtime_types.ContextMessageRole.ASSISTANT,
                        content=[
                            runtime_types.ContextMessageContentItem_Text(
                                content=full_content
                            )
                        ],
                        tool_calls=[],
                    ),
                    ctx,
                )

            # TODO look at the finished/ctx.complete() logic here
            except asyncio.CancelledError:
                finished_source.push_item(runtime_types.Trigger(), ctx)
                ctx.complete()
            except Exception as e:
                logging.error(f"Error during LLM generation: {e}", exc_info=e)
                finished_source.push_item(runtime_types.Trigger(), ctx)
                ctx.complete()
            finally:
                finished_source.push_item(runtime_types.Trigger(), ctx)
                ctx.complete()

        def done_callback(task: asyncio.Task):
            nonlocal running_handle
            if task.exception() is not None:
                logging.error(f"Generation task failed: {task.exception()}")
            else:
                logging.info("Generation task completed successfully.")
            running_handle = None

        cancel_task_t = asyncio.create_task(cancel_task())
        async for item in run_trigger:
            ctx = item.ctx
            messages = context_sink.get_value()
            request = LLMRequest(context=messages, tool_definitions=[])
            if running_handle is not None:
                logging.warning(
                    "LLM is already running a generation, skipping new request."
                )
                ctx.complete()
                continue

            try:
                running_handle = await self.llm.create_completion(
                    request=request, mode="qwen_omni"
                )
                t = asyncio.create_task(generation_task(running_handle, ctx))
                tasks.add(t)
                t.add_done_callback(done_callback)
            except Exception as e:
                logging.error(f"Failed to start LLM generation: {e}", exc_info=e)
                finished_source.push_item(runtime_types.Trigger(), ctx)
        await cancel_task_t
