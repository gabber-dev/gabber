# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import Any, cast

from gabber.core import pad
from gabber.core.node import NodeMetadata
from gabber.core.types import pad_constraints

from .base_llm import BaseLLM
from gabber.lib.llm import (
    OPENAI_TOKEN_ESTIMATOR,
    DEFAULT_TOKEN_ESTIMATOR,
)


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

    def get_token_estimator(self) -> Any:
        if "openai" in self.model():
            return OPENAI_TOKEN_ESTIMATOR

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
        base_sink_pads, base_source_pads = self.get_base_pads()
        base_url_sink = cast(pad.PropertySinkPad, self.get_pad("base_url"))
        if not base_url_sink:
            base_url_sink = pad.PropertySinkPad(
                id="base_url",
                group="base_url",
                owner_node=self,
                default_type_constraints=[pad_constraints.String()],
                value="https://api.openai.com/v1",
            )

        api_key_sink = cast(pad.PropertySinkPad, self.get_pad("api_key"))
        if not api_key_sink:
            api_key_sink = pad.PropertySinkPad(
                id="api_key",
                group="api_key",
                owner_node=self,
                default_type_constraints=[pad_constraints.Secret(options=[])],
                value="",
            )

        model_sink = cast(pad.PropertySinkPad, self.get_pad("model"))
        if not model_sink:
            model_sink = pad.PropertySinkPad(
                id="model",
                group="model",
                owner_node=self,
                default_type_constraints=[pad_constraints.String()],
                value="gpt-4.1-mini",
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

        base_sink_pads.extend(
            [base_url_sink, api_key_sink, model_sink, context_len_sink]
        )

        cast(list[pad_constraints.Secret], api_key_sink.get_type_constraints())[
            0
        ].options = self.secrets

        self.pads = cast(list[pad.Pad], base_sink_pads + base_source_pads)
