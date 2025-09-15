# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from core import pad
import os
from core.node import NodeMetadata
from nodes.llm import BaseLLM


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

    def resolve_pads(self):
        sink, source = self.get_base_pads()
        port_pad = cast(pad.PropertySinkPad, self.get_pad("port"))
        if not port_pad:
            port_pad = pad.PropertySinkPad(
                id="port",
                group="port",
                owner_node=self,
                default_type_constraints=[pad.types.Integer()],
                value=7002,
            )

        self.pads = cast(list[pad.Pad], sink + [port_pad] + source)
