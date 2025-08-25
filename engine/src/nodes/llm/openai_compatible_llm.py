# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from core import pad
from core.node import NodeMetadata

from .base_llm import BaseLLM


class OpenAICompatibleLLM(BaseLLM):
    @classmethod
    def get_description(cls) -> str:
        return "Send and receive responses from any OpenAI-compatible language model"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="ai", secondary="llm", tags=["completion", "text", "openai"]
        )

    def supports_tool_calls(self) -> bool:
        return True

    def base_url(self) -> str:
        base_url_pad = cast(pad.PropertySinkPad, self.get_pad_required("base_url"))
        base_url_value = base_url_pad.get_value()

        if isinstance(base_url_value, str):
            return base_url_value
        else:
            return "https://api.openai.com/v1"

    def model(self) -> str:
        model_pad = cast(pad.PropertySinkPad, self.get_pad_required("model"))
        model_value = model_pad.get_value()
        return model_value if isinstance(model_value, str) else "gpt-4.1-mini"

    async def api_key(self) -> str:
        api_key_pad = cast(pad.PropertySinkPad, self.get_pad_required("api_key"))
        api_key_name = api_key_pad.get_value()
        if not isinstance(api_key_name, str):
            raise ValueError("API key must be a string.")
        if not self.secret_provider:
            raise RuntimeError("Secret provider is not set for OpenAICompatibleLLM.")
        return await self.secret_provider.resolve_secret(api_key_name)

    async def resolve_pads(self):
        await super().resolve_pads()
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

        cast(list[pad.types.Secret], api_key_sink.get_type_constraints())[
            0
        ].options = self.secrets
