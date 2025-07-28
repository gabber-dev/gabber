# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from core import node, pad
from core.node import NodeMetadata


class SetToolResult(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Sets the result of a tool call for LLM processing"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="ai", secondary="tools", tags=["result", "set"])

    async def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("result"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="result",
                owner_node=self,
                type_constraints=[pad.types.String(max_length=1024)],
                group="result",
            )
            self.pads.append(sink)

    async def run(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad_required("result"))
        async for item in sink:
            v, ctx = item.value, item.ctx
            originator = ctx.find_parent_by_originator("tool_call")
            if originator:
                originator.append_result(item.value)
            else:
                raise ValueError("No originator found in context for tool call result.")
            ctx.complete()
