# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from gabber.core import pad
import os
from gabber.core.node import NodeMetadata
from gabber.nodes.llm import BaseLLM
from gabber.lib.llm.token_estimator import TokenEstimator, DEFAULT_TOKEN_ESTIMATOR
from gabber.core.types import pad_constraints


class LocalLLM(BaseLLM):
    @classmethod
    def get_description(cls) -> str:
        return "Send and receive responses from any Qwen-omni language model"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="ai", secondary="local", tags=["completion", "text", "qwen-omni"]
        )

    def supports_tool_calls(self) -> bool:
        return True

    def base_url(self) -> str:
        port_pad = cast(pad.PropertySinkPad, self.get_pad_required("port"))
        port_value = port_pad.get_value()
        if not isinstance(port_value, int):
            port_value = 7002

        host = os.environ.get("LOCAL_LLM_HOST", "localhost")

        return f"http://{host}:{port_value}/v1"

    def model(self) -> str:
        return ""

    async def api_key(self) -> str:
        return ""

    def get_token_estimator(self) -> TokenEstimator:
        return DEFAULT_TOKEN_ESTIMATOR

    async def max_context_len(self) -> int:
        context_len_pad = cast(
            pad.PropertySinkPad, self.get_pad_required("max_context_len")
        )
        context_len_value = context_len_pad.get_value()
        if isinstance(context_len_value, int) and context_len_value >= 4096:
            return context_len_value

        self.logger.warning(
            "Invalid max_context_len value; defaulting to 32768. It must be an integer >= 4096."
        )
        return 32768

    def resolve_pads(self):
        sink, source = self.get_base_pads()
        port_pad = cast(pad.PropertySinkPad, self.get_pad("port"))
        if not port_pad:
            port_pad = pad.PropertySinkPad(
                id="port",
                group="port",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer()],
                value=7002,
            )

        context_len_sink = cast(pad.PropertySinkPad, self.get_pad("max_context_len"))
        if not context_len_sink:
            context_len_sink = pad.PropertySinkPad(
                id="max_context_len",
                group="max_context_len",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer(minimum=4096)],
                value=32768,
            )

        self.pads = cast(list[pad.Pad], sink + [port_pad, context_len_sink] + source)
