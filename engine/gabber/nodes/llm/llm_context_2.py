# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from gabber.core import node, pad
from gabber.core.types import runtime
from gabber.core.types import pad_constraints

DEFAULT_SYSTEM_MESSAGE = runtime.ContextMessage(
    role=runtime.ContextMessageRole.SYSTEM,
    content=[
        runtime.ContextMessageContentItem_Text(content="You are a helpful assistant.")
    ],
    tool_calls=[],
)


class LLMContext2(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Manages conversation context for language models"

    @classmethod
    def get_metadata(cls) -> node.NodeMetadata:
        return node.NodeMetadata(
            primary="ai", secondary="llm", tags=["context", "memory"]
        )

    def resolve_pads(self):
        new_user_message = cast(
            pad.StatelessSourcePad, self.get_pad("new_user_message")
        )
        if not new_user_message:
            new_user_message = pad.StatelessSourcePad(
                id="new_user_message",
                group="new_user_message",
                owner_node=self,
                default_type_constraints=[pad_constraints.ContextMessage()],
            )

        system_message = cast(pad.PropertySinkPad, self.get_pad("system_message"))
        if not system_message:
            system_message = pad.PropertySinkPad(
                id="system_message",
                group="system_message",
                owner_node=self,
                default_type_constraints=[pad_constraints.ContextMessage()],
                value=DEFAULT_SYSTEM_MESSAGE,
            )

        source = cast(pad.PropertySourcePad, self.get_pad("source"))
        if not source:
            source = pad.PropertySourcePad(
                id="source",
                group="source",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.List(
                        item_type_constraints=[pad_constraints.ContextMessage()]
                    )
                ],
                value=[system_message.get_value()],
            )

        source.set_value([system_message.get_value()])

        self.pads = cast(
            list[pad.Pad],
            [] + [source],
        )
