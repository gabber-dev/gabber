# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from typing import cast

from gabber.core import node, pad
from gabber.core.node import NodeMetadata, NodeNote


class ChatInput(node.Node):
    type = "ChatInput"

    @classmethod
    def get_description(cls) -> str:
        return "A chat input node to send text into your Gabber flow"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="debug", tags=["input", "text"])

    def resolve_pads(self):
        output = cast(pad.StatelessSourcePad | None, self.get_pad("output"))
        if output is None:
            output = pad.StatelessSourcePad(
                id="output",
                owner_node=self,
                group="text",
                default_type_constraints=[pad_constraints.String()],
            )

        self.pads = [output]

    def get_notes(self) -> list[NodeNote]:
        audio_pad = cast(pad.StatelessSinkPad, self.get_pad("audio"))
        video_pad = cast(pad.StatelessSinkPad, self.get_pad("video"))
        notes: list[NodeNote] = []
        any_connections = False

        if audio_pad and audio_pad.get_previous_pad():
            any_connections = True

        if video_pad and video_pad.get_previous_pad():
            any_connections = True

        if not any_connections:
            notes.append(
                NodeNote(
                    level="warning",
                    message="Output node has no connected pads. No media will be sent to the user.",
                )
            )

        return notes

    async def run(self):
        pass
