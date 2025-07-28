# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import time
from typing import cast

from core import node, pad, runtime_types
from core.node import NodeMetadata
from lib.llm import AsyncLLMResponseHandle, LLMRequest, openai_compatible
from utils import get_full_content_from_deltas, get_tool_calls_from_choice_deltas

from nodes.core.tool import Tool, ToolGroup


class OpenAICompatibleLLM(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Send and receive responses from any OpenAI-compatible language model"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="ai", secondary="llm", tags=["completion", "text", "openai"]
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

        tool_calls_started_source = cast(
            pad.StatelessSourcePad, self.get_pad("tool_calls_started")
        )
        if not tool_calls_started_source:
            tool_calls_started_source = pad.StatelessSourcePad(
                id="tool_calls_started",
                group="tool_calls_started",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(tool_calls_started_source)

        tool_calls_finished_source = cast(
            pad.StatelessSourcePad, self.get_pad("tool_calls_finished")
        )
        if not tool_calls_finished_source:
            tool_calls_finished_source = pad.StatelessSourcePad(
                id="tool_calls_finished",
                group="tool_calls_finished",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(tool_calls_finished_source)

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
                value="https://api.openai.com/v1",
            )
            self.pads.append(base_url_sink)

        api_key_sink = cast(pad.PropertySinkPad, self.get_pad("api_key"))
        if not api_key_sink:
            api_key_sink = pad.PropertySinkPad(
                id="api_key",
                group="api_key",
                owner_node=self,
                type_constraints=[pad.types.Secret(options=[])],
                value="",
            )
            self.pads.append(api_key_sink)

        model_sink = cast(pad.PropertySinkPad, self.get_pad("model"))
        if not model_sink:
            model_sink = pad.PropertySinkPad(
                id="model",
                group="model",
                owner_node=self,
                type_constraints=[pad.types.String()],
                value="gpt-4.1-mini",
            )
            self.pads.append(model_sink)

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

        tool_group_sink = cast(pad.PropertySinkPad, self.get_pad("tool_group"))
        if not tool_group_sink:
            tool_group_sink = pad.PropertySinkPad(
                id="tool_group",
                group="tool_group",
                owner_node=self,
                type_constraints=[pad.types.NodeReference(node_types=["ToolGroup"])],
                value=None,
            )
            self.pads.append(tool_group_sink)

        cast(list[pad.types.Secret], api_key_sink.get_type_constraints())[
            0
        ].options = self.secrets

    async def run(self):
        api_key_sink = cast(pad.PropertySinkPad, self.get_pad_required("api_key"))
        base_url_sink = cast(pad.PropertySinkPad, self.get_pad_required("base_url"))
        model_sink = cast(pad.PropertySinkPad, self.get_pad_required("model"))
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
        tool_calls_started_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("tool_calls_started")
        )
        tool_calls_finished_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("tool_calls_finished")
        )
        context_sink = cast(pad.PropertySinkPad, self.get_pad_required("context"))
        context_message_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("context_message")
        )
        tool_group_sink = cast(pad.PropertySinkPad, self.get_pad_required("tool_group"))
        run_trigger = cast(pad.StatelessSinkPad, self.get_pad_required("run_trigger"))
        api_key_secret_id = api_key_sink.get_value()
        if not self.secret_provider:
            raise RuntimeError("Secret provider is not set for OpenAICompatibleLLM.")

        self.api_key = await self.secret_provider.resolve_secret(api_key_secret_id)
        self.llm = openai_compatible.OpenAICompatibleLLM(
            base_url=base_url_sink.get_value(),
            api_key=self.api_key,
            headers={},
            model=model_sink.get_value(),
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
            tool_task: asyncio.Task[list[str]] | None = None
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

                all_tool_calls = get_tool_calls_from_choice_deltas(all_deltas)
                if len(all_tool_calls) > 0:
                    tool_calls_started_source.push_item(runtime_types.Trigger(), ctx)
                    tg = cast(ToolGroup, tool_group_sink.get_value())
                    tool_task = asyncio.create_task(tg.call_tools(all_tool_calls, ctx))

                context_message_source.push_item(
                    runtime_types.ContextMessage(
                        role=runtime_types.ContextMessageRole.ASSISTANT,
                        content=[
                            runtime_types.ContextMessageContentItem_Text(
                                content=get_full_content_from_deltas(all_deltas)
                            )
                        ],
                        tool_calls=all_tool_calls,
                    ),
                    ctx,
                )

                if tool_task is not None:
                    tool_results = await tool_task
                    for i in range(len(all_tool_calls)):
                        context_message_source.push_item(
                            runtime_types.ContextMessage(
                                role=runtime_types.ContextMessageRole.TOOL,
                                content=[
                                    runtime_types.ContextMessageContentItem_Text(
                                        content=tool_results[i]
                                    )
                                ],
                                tool_call_id=all_tool_calls[i].call_id,
                                tool_calls=[],
                            ),
                            ctx,
                        )
                    tool_calls_finished_source.push_item(runtime_types.Trigger(), ctx)
            # TODO look at the finished/ctx.complete() logic here
            except asyncio.CancelledError:
                finished_source.push_item(runtime_types.Trigger(), ctx)
                ctx.complete()
            except Exception as e:
                logging.error(f"Error during LLM generation: {e}", exc_info=e)
                if tool_task is not None:
                    tool_calls_finished_source.push_item(runtime_types.Trigger(), ctx)

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
            tool_definitions: list[runtime_types.ToolDefinition] = []
            if tool_group_sink.get_value() is not None:
                tool_nodes = cast(ToolGroup, tool_group_sink.get_value()).tool_nodes
                for tn in tool_nodes:
                    if not isinstance(tn, Tool):
                        logging.warning(f"Node {tn.id} is not a Tool, skipping.")
                        continue
                    td = tn.get_tool_definition()
                    tool_definitions.append(td)
            request = LLMRequest(context=messages, tool_definitions=tool_definitions)
            if running_handle is not None:
                logging.warning(
                    "LLM is already running a generation, skipping new request."
                )
                continue

            try:
                running_handle = await self.llm.create_completion(request=request)
                t = asyncio.create_task(generation_task(running_handle, ctx))
                tasks.add(t)
                t.add_done_callback(done_callback)
            except Exception as e:
                logging.error(f"Failed to start LLM generation: {e}", exc_info=e)
                finished_source.push_item(runtime_types.Trigger(), ctx)
        await cancel_task_t
