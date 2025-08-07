# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from core import node, pad
from core.node import NodeMetadata

logger = logging.getLogger(__name__)


class ChatInput(node.Node):
    type = "ChatInput"

    @classmethod
    def get_description(cls) -> str:
        return "A chat input node to send text into your Gabber flow"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core",
            secondary="debug",
            tags=["input", "text"]
        )

    async def resolve_pads(self):
        logger.info("[ChatInput] Resolving pads for node %s", self.id)
        output = cast(pad.StatelessSourcePad, self.get_pad("output"))
        if not output:
            logger.info("[ChatInput] Creating output pad")
            output = pad.StatelessSourcePad(
                id="output",
                owner_node=self,
                group="text",
                type_constraints=[pad.types.String()],
            )
            self.pads.append(output)
            logger.info("[ChatInput] Created output pad: %s", output)

    async def run(self):
        logger.info("[ChatInput] Starting run for node %s", self.id)
        output = cast(pad.StatelessSourcePad, self.get_pad_required("output"))
        logger.info("[ChatInput] Got output pad: %s", output)
        
        # The actual message sending is handled by the frontend component
        # We just need to ensure the value is properly handled
        try:
            async for item in output:
                try:
                    logger.info("[ChatInput] Received item: %s", item)
                    if isinstance(item.value, dict) and 'value' in item.value:
                        # Extract the text from the frontend's value object
                        text = item.value['value']
                        if text is not None:
                            logger.info("[ChatInput] Sending text: %s", text)
                            # Create a new pad item with the text value
                            output.push_item(text, item.ctx)
                    item.ctx.complete()
                except Exception as e:
                    logger.error("[ChatInput] Error handling item: %s", e)
        except Exception as e:
            logger.error("[ChatInput] Error in run loop: %s", e)