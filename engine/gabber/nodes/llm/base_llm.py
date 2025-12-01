# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from abc import ABC, abstractmethod
from typing import cast

from gabber.core import node, pad, editor
from gabber.core.types import runtime
from gabber.nodes.core.tool import mcp
from gabber.lib.llm import AsyncLLMResponseHandle, LLMRequest, openai_compatible
from gabber.utils import get_full_content_from_deltas, get_tool_calls_from_choice_deltas
from gabber.nodes.core.tool import ToolGroup
from mcp.types import TextContent
from gabber.lib.llm.token_estimator import TokenEstimator
from gabber.core.types import pad_constraints


class BaseLLM(node.Node, ABC):
    @abstractmethod
    def supports_tool_calls(self) -> bool: ...

    @abstractmethod
    def base_url(self) -> str: ...

    @abstractmethod
    def model(self) -> str: ...

    @abstractmethod
    async def api_key(self) -> str: ...

    @abstractmethod
    async def max_context_len(self) -> int: ...

    @abstractmethod
    def get_token_estimator(self) -> TokenEstimator: ...

    def get_base_pads(self):
        run_trigger = cast(pad.StatelessSinkPad, self.get_pad("run_trigger"))
        if not run_trigger:
            run_trigger = pad.StatelessSinkPad(
                id="run_trigger",
                group="run_trigger",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        started_source = cast(pad.StatelessSourcePad, self.get_pad("started"))
        if not started_source:
            started_source = pad.StatelessSourcePad(
                id="started",
                group="started",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        tool_calls_started_source = cast(
            pad.StatelessSourcePad, self.get_pad("tool_calls_started")
        )
        if not tool_calls_started_source:
            tool_calls_started_source = pad.StatelessSourcePad(
                id="tool_calls_started",
                group="tool_calls_started",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        tool_calls_finished_source = cast(
            pad.StatelessSourcePad, self.get_pad("tool_calls_finished")
        )
        if not tool_calls_finished_source:
            tool_calls_finished_source = pad.StatelessSourcePad(
                id="tool_calls_finished",
                group="tool_calls_finished",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        first_token_source = cast(pad.StatelessSourcePad, self.get_pad("first_token"))
        if not first_token_source:
            first_token_source = pad.StatelessSourcePad(
                id="first_token",
                group="first_token",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        text_stream_source = cast(pad.StatelessSourcePad, self.get_pad("text_stream"))
        if not text_stream_source:
            text_stream_source = pad.StatelessSourcePad(
                id="text_stream",
                group="text_stream",
                owner_node=self,
                default_type_constraints=[pad_constraints.TextStream()],
            )

        thinking_stream_source = cast(
            pad.StatelessSourcePad, self.get_pad("thinking_stream")
        )
        if not thinking_stream_source:
            thinking_stream_source = pad.StatelessSourcePad(
                id="thinking_stream",
                group="thinking_stream",
                owner_node=self,
                default_type_constraints=[pad_constraints.TextStream()],
            )

        context_message_source = cast(
            pad.StatelessSourcePad, self.get_pad("context_message")
        )
        if not context_message_source:
            context_message_source = pad.StatelessSourcePad(
                id="context_message",
                group="context_message",
                owner_node=self,
                default_type_constraints=[pad_constraints.ContextMessage()],
            )

        finished_source = cast(pad.StatelessSourcePad, self.get_pad("finished"))
        if not finished_source:
            finished_source = pad.StatelessSourcePad(
                id="finished",
                group="finished",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        cancel_trigger = cast(pad.StatelessSinkPad, self.get_pad("cancel_trigger"))
        if not cancel_trigger:
            cancel_trigger = pad.StatelessSinkPad(
                id="cancel_trigger",
                group="cancel_trigger",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        context_sink = self.get_property_sink_pad(
            list[runtime.ContextMessage], "context"
        )
        if not context_sink:
            context_sink = pad.PropertySinkPad(
                id="context",
                group="context",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.List(
                        item_type_constraints=[pad_constraints.ContextMessage()]
                    )
                ],
                value=[
                    runtime.ContextMessage(
                        role=runtime.ContextMessageRoleEnum.SYSTEM,
                        content=[
                            runtime.ContextMessageContentItem_Text(
                                content="You are a helpful assistant."
                            )
                        ],
                        tool_calls=[],
                    )
                ],
            )

        tool_group_sink = cast(pad.PropertySinkPad, self.get_pad("tool_group"))
        mcp_pads: list[pad.PropertySinkPad] = []
        if self.supports_tool_calls():
            if not tool_group_sink:
                tool_group_sink = pad.PropertySinkPad(
                    id="tool_group",
                    group="tool_group",
                    owner_node=self,
                    default_type_constraints=[
                        pad_constraints.NodeReference(node_types=["ToolGroup"])
                    ],
                    value=None,
                )

            mcp_pads = self.mcp_server_pads()

        base_sink_pads: list[pad.SinkPad] = [
            run_trigger,
            cancel_trigger,
            context_sink,
        ]
        base_source_pads: list[pad.SourcePad] = [
            started_source,
            first_token_source,
            text_stream_source,
            thinking_stream_source,
            context_message_source,
            finished_source,
        ]

        if tool_group_sink is not None:
            base_sink_pads.append(tool_group_sink)
            base_sink_pads += mcp_pads
            base_source_pads.append(tool_calls_started_source)
            base_source_pads.append(tool_calls_finished_source)

        return base_sink_pads, base_source_pads

    def mcp_server_pads(self):
        exising_mcp_pads = [
            p
            for p in self.pads
            if isinstance(p, pad.PropertySinkPad)
            and p.get_id().startswith("mcp_server_")
        ]

        connected_mcp_pads = [
            p for p in exising_mcp_pads if p.get_previous_pad() is not None
        ]

        renamed_connected_mcp_pads = []
        for i, cp in enumerate(connected_mcp_pads):
            new_id = f"mcp_server_{i}"
            if cp.get_id() != new_id:
                cp.set_id(new_id)
            renamed_connected_mcp_pads.append(cp)

        empty_pad = pad.PropertySinkPad(
            id=f"mcp_server_{len(renamed_connected_mcp_pads)}",
            group="mcp_server",
            owner_node=self,
            default_type_constraints=[
                pad_constraints.NodeReference(node_types=["MCP"]),
            ],
            value="None",
        )

        return renamed_connected_mcp_pads + [empty_pad]

    async def run(self):
        cancel_trigger = cast(
            pad.StatelessSinkPad, self.get_pad_required("cancel_trigger")
        )
        thinking_stream_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("thinking_stream")
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

        # Get tool call source pads if tool calling is supported
        tool_calls_started_source: pad.StatelessSourcePad | None = None
        tool_calls_finished_source: pad.StatelessSourcePad | None = None
        if self.supports_tool_calls():
            tool_calls_started_source = cast(
                pad.StatelessSourcePad, self.get_pad_required("tool_calls_started")
            )
            tool_calls_finished_source = cast(
                pad.StatelessSourcePad, self.get_pad_required("tool_calls_finished")
            )

        api_key = await self.api_key()
        llm = openai_compatible.OpenAICompatibleLLM(
            base_url=self.base_url(),
            api_key=api_key,
            headers={},
            model=self.model(),
            max_context_len=await self.max_context_len(),
            token_estimator=self.get_token_estimator(),
        )

        # Retry loop in case the LLM is still starting up
        video_supported = False
        RETRY_LIMIT = 20
        for i in range(RETRY_LIMIT):
            if i == RETRY_LIMIT - 1:
                self.logger.error("Failed to check video support after 20 attempts.")
                video_supported = False
                break

            try:
                video_supported = await self._supports_video(llm)
                break
            except Exception:
                self.logger.error(
                    "Failed to check video support, trying again in 5s", exc_info=True
                )

            await asyncio.sleep(5)

        audio_supported = await self._supports_audio(llm)

        self.logger.info(
            f"LLM supports video: {video_supported} audio: {audio_supported}"
        )

        running_handle: AsyncLLMResponseHandle | None = None
        tasks: set[asyncio.Task] = set()

        async def cancel_task():
            nonlocal running_handle
            async for item in cancel_trigger:
                self.logger.info("Cancelling LLM generation request.")
                if running_handle is not None:
                    running_handle.cancel()
                item.ctx.complete()

        async def generation_task(
            handle: AsyncLLMResponseHandle,
            ctx: pad.RequestContext,
            tg_tools: list[runtime.ToolDefinition],
            mcp_tools: dict[mcp.MCP, list[runtime.ToolDefinition]],
            estimated_prompt_tokens: int,
        ):
            tool_task: asyncio.Task[list[runtime.ContextMessage]] | None = None
            all_deltas: list[runtime.ContextMessageContent_ChoiceDelta] = []
            text_stream = runtime.TextStream()
            thinking_stream = runtime.TextStream()
            thinking_stream_source.push_item(thinking_stream, ctx)
            text_stream_source.push_item(text_stream, ctx)
            try:
                started_source.push_item(runtime.Trigger(), ctx)
                thinking = False
                async for item in handle:
                    if item.usage is not None:
                        self.logger.info(
                            f"Actual prompt usage: {item.usage.get('prompt_tokens', 0)}, estimated: {estimated_prompt_tokens}"
                        )
                    if item.refusal is not None:
                        continue
                    if item.content:
                        cnt = item.content
                        if thinking:
                            split = cnt.split("</think>")
                            if len(split) == 2:
                                thinking_cnt = split[0]
                                normal_cnt = split[1]
                                thinking_stream.push_text(thinking_cnt)
                                text_stream.push_text(normal_cnt)
                                thinking = False
                            else:
                                thinking_stream.push_text(cnt)
                        else:
                            split = cnt.split("<think>")
                            if len(split) == 2:
                                normal_cnt = split[0]
                                thinking_cnt = split[1]
                                thinking_stream.push_text(thinking_cnt)
                                text_stream.push_text(normal_cnt)
                                thinking = True
                            else:
                                text_stream.push_text(cnt)

                    all_deltas.append(item)

                thinking_stream.eos()
                text_stream.eos()

                all_tool_calls = get_tool_calls_from_choice_deltas(all_deltas)
                self.logger.info(f"NEIL Detected tool calls: {all_tool_calls}")
                if all_tool_calls:
                    if tool_calls_started_source:
                        tool_calls_started_source.push_item(runtime.Trigger(), ctx)
                    tool_task = asyncio.create_task(
                        self.call_tools(
                            all_tool_calls=all_tool_calls,
                            tg_tool_defns=tg_tools,
                            mcp_tool_defns=mcp_tools,
                            ctx=ctx,
                        )
                    )

                full_content = get_full_content_from_deltas(all_deltas)
                context_message_source.push_item(
                    runtime.ContextMessage(
                        role=runtime.ContextMessageRoleEnum.ASSISTANT,
                        content=[
                            runtime.ContextMessageContentItem_Text(content=full_content)
                        ],
                        tool_calls=all_tool_calls,
                        tool_call_id=all_tool_calls[0].call_id
                        if all_tool_calls
                        else None,
                    ),
                    ctx,
                )

                if tool_task is not None:
                    tool_msgs = await tool_task
                    for msg in tool_msgs:
                        context_message_source.push_item(msg, ctx)
                    if tool_calls_finished_source:
                        tool_calls_finished_source.push_item(runtime.Trigger(), ctx)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                self.logger.error(f"Error during LLM generation: {e}", exc_info=e)
            finally:
                finished_source.push_item(runtime.Trigger(), ctx)
                ctx.complete()

        def done_callback(task: asyncio.Task):
            nonlocal running_handle
            if task.exception() is not None:
                self.logger.error(f"Generation task failed: {task.exception()}")
            else:
                self.logger.info("Generation task completed successfully.")
            running_handle = None

        cancel_task_t = asyncio.create_task(cancel_task())
        async for item in run_trigger:
            ctx = item.ctx
            messages = context_sink.get_value()
            assert isinstance(messages, list)
            messages = cast(list[runtime.ContextMessage], messages)
            all_tool_definitions: list[runtime.ToolDefinition] = []
            tg_tool_definitions: list[runtime.ToolDefinition] = []

            tool_group_node = self.get_tool_group_node()
            if tool_group_node is not None:
                tg_tool_definitions = cast(
                    ToolGroup, tool_group_node
                ).list_tool_definitions()
                all_tool_definitions.extend(tg_tool_definitions)

            mcp_tool_definitions: dict[mcp.MCP, list[runtime.ToolDefinition]] = {}
            mcp_sinks = self.mcp_server_pads()
            for mcp_sink in mcp_sinks:
                mcp_node = cast(mcp.MCP, mcp_sink.get_value())
                if not isinstance(mcp_node, mcp.MCP):
                    continue
                if mcp_node not in mcp_tool_definitions:
                    mcp_tool_definitions[mcp_node] = []
                try:
                    tdfs = await mcp_node.to_tool_definitions()
                    mcp_tool_definitions[mcp_node].extend(tdfs)
                    all_tool_definitions.extend(tdfs)
                except Exception as e:
                    self.logger.error(
                        f"BaseLLM: Failed to get tool definitions from MCP node {mcp_node.id}: {e}"
                    )

            request = LLMRequest(
                context=messages, tool_definitions=all_tool_definitions
            )
            self.logger.info(f"Starting LLM generation: {request}")
            if running_handle is not None:
                self.logger.warning(
                    "LLM is already running a generation, skipping new request."
                )
                ctx.complete()
                continue

            try:
                estimated_prompt_tokens = request.estimate_tokens(
                    token_estimator=self.get_token_estimator()
                )
                running_handle = await llm.create_completion(
                    request=request,
                    video_support=video_supported,
                    audio_support=audio_supported,
                )
                t = asyncio.create_task(
                    generation_task(
                        running_handle,
                        ctx,
                        tg_tool_definitions,
                        {},
                        estimated_prompt_tokens=estimated_prompt_tokens,
                    )
                )
                tasks.add(t)
                t.add_done_callback(done_callback)
            except Exception as e:
                self.logger.error(f"Failed to start LLM generation: {e}", exc_info=e)
                finished_source.push_item(runtime.Trigger(), ctx)
        await cancel_task_t

    def get_tool_group_node(self) -> ToolGroup | None:
        if not self.supports_tool_calls():
            return None
        tool_group_sink = cast(pad.PropertySinkPad, self.get_pad_required("tool_group"))
        tool_group_sink_value = tool_group_sink.get_value()
        if tool_group_sink_value is None:
            return None
        assert isinstance(tool_group_sink_value, runtime.NodeReference)
        tg_node = self.graph.get_node(tool_group_sink_value.node_id)
        if not isinstance(tg_node, ToolGroup):
            return None
        return tg_node

    async def call_tools(
        self,
        *,
        tg_tool_defns: list[runtime.ToolDefinition],
        mcp_tool_defns: dict[mcp.MCP, list[runtime.ToolDefinition]],
        all_tool_calls: list[runtime.ToolCall],
        ctx: pad.RequestContext,
    ) -> list[runtime.ContextMessage]:
        tg_tool_calls = [
            t for t in all_tool_calls if t.name in [td.name for td in tg_tool_defns]
        ]

        results: list[runtime.ContextMessage] = []

        all_tasks: list[asyncio.Task] = []

        async def run_tg_task():
            tg_res = await self.call_tg_calls(tg_tool_calls=tg_tool_calls, ctx=ctx)
            for i, res in enumerate(tg_res):
                msg = runtime.ContextMessage(
                    role=runtime.ContextMessageRoleEnum.TOOL,
                    content=[runtime.ContextMessageContentItem_Text(content=res)],
                    tool_call_id=tg_tool_calls[i].call_id,
                    tool_calls=[],
                )
                results.append(msg)

        async def run_mcp_task(node: mcp.MCP, tc: runtime.ToolCall):
            res = await node.call_tool(tc)
            if isinstance(res, Exception):
                msg = runtime.ContextMessage(
                    role=runtime.ContextMessageRoleEnum.TOOL,
                    content=[
                        runtime.ContextMessageContentItem_Text(
                            content=f"Error calling tool '{tc.name}': {res}"
                        )
                    ],
                    tool_call_id=tc.call_id,
                    tool_calls=[],
                )
            else:
                contents: list[runtime.ContextMessageContentItem] = []
                for block in res:
                    if isinstance(block, TextContent):
                        content = runtime.ContextMessageContentItem_Text(
                            content=block.text
                        )
                        contents.append(content)
                msg = runtime.ContextMessage(
                    role=runtime.ContextMessageRoleEnum.TOOL,
                    content=contents,
                    tool_call_id=tc.call_id,
                    tool_calls=[],
                )
            results.append(msg)

        if len(tg_tool_calls) > 0:
            self.logger.info(
                f"BaseLLM: Creating TG task for {len(tg_tool_calls)} tool calls"
            )
            tg_task = asyncio.create_task(run_tg_task())
            all_tasks.append(tg_task)

        for mcp_node in mcp_tool_defns.keys():
            mcp_defns = mcp_tool_defns[mcp_node]
            mcp_defn_names = [td.name for td in mcp_defns]
            mcp_calls = [tc for tc in all_tool_calls if tc.name in mcp_defn_names]
            for tc in mcp_calls:
                mcp_t = asyncio.create_task(run_mcp_task(mcp_node, tc))
                all_tasks.append(mcp_t)

        await asyncio.gather(*all_tasks)
        return results

    async def call_tg_calls(self, tg_tool_calls: list[runtime.ToolCall], ctx):
        tool_group_node = self.get_tool_group_node()
        if not tool_group_node:
            raise RuntimeError("Tool group node not found")
        return await tool_group_node.call_tools(tg_tool_calls, ctx)

    def get_notes(self) -> list[node.NodeNote]:
        notes: list[node.NodeNote] = []
        run_trigger = cast(pad.StatelessSinkPad, self.get_pad("run_trigger"))
        if not run_trigger or run_trigger.get_previous_pad() is None:
            notes.append(
                node.NodeNote(
                    level="warning",
                    message="Run Trigger pad is not connected. This node will never execute.",
                    pad="run_trigger",
                )
            )

        context_sink = cast(pad.PropertySinkPad, self.get_pad("context"))
        if not context_sink or context_sink.get_previous_pad() is None:
            notes.append(
                node.NodeNote(
                    level="warning",
                    message="Context pad is not connected. The LLM is unable to run without an LLMContext.",
                    pad="context",
                    recommendations=[
                        editor.models.NodeNoteRecommendation(
                            message="Create an LLMContext and connect it to the context pad.",
                            edits=[
                                editor.models.InsertNodeEdit(
                                    node_type="LLMContext",
                                    editor_dimensions=(10, 10),
                                    editor_position=(0, 0),
                                    editor_name="LLMContext",
                                ),
                            ],
                        )
                    ],
                )
            )

        return notes

    async def _supports_video(self, llm: openai_compatible.OpenAICompatibleLLM) -> bool:
        self.logger.info("Checking if LLM supports video...")
        dummy_request = LLMRequest(
            context=[
                runtime.ContextMessage(
                    role=runtime.ContextMessageRoleEnum.SYSTEM,
                    content=[
                        runtime.ContextMessageContentItem_Text(content="."),
                        runtime.ContextMessageContentItem_Video(
                            clip=runtime.VideoClip(
                                video=[runtime.VideoFrame.black_frame(16, 16, 0.0)] * 10
                            )
                        ),
                    ],
                    tool_calls=[],
                )
            ],
            tool_definitions=[],
        )
        try:
            handle = await llm.create_completion(
                request=dummy_request,
                video_support=True,
                audio_support=False,
                max_completion_tokens=1,
            )
            async for _ in handle:
                pass
        except openai_compatible.OpenAICompatibleLLMError as e:
            self.logger.info(
                f"Video support check failed with error code: {e.code}, {e.msg}"
            )
            if e.code == 500 or e.code == 400:
                return False

            raise e
        except Exception as e:
            raise e

        return True

    async def _supports_audio(self, llm: openai_compatible.OpenAICompatibleLLM) -> bool:
        return False
        dummy_request = LLMRequest(
            context=[
                runtime.ContextMessage(
                    role=runtime.ContextMessageRoleEnum.SYSTEM,
                    content=[
                        runtime.ContextMessageContentItem_Text(content="."),
                        runtime.ContextMessageContentItem_Audio(
                            clip=runtime.AudioClip(
                                audio=[runtime.AudioFrame.silence(0.1)]
                            )
                        ),
                    ],
                    tool_calls=[],
                )
            ],
            tool_definitions=[],
        )
        try:
            handle = await llm.create_completion(
                request=dummy_request,
                video_support=False,
                audio_support=True,
                max_completion_tokens=1,
            )
            async for _ in handle:
                pass
        except openai_compatible.OpenAICompatibleLLMError as e:
            if e.code == 500 or e.code == 400:
                return False

            raise e
        except Exception as e:
            raise e

        return True
