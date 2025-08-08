# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import json
from typing import cast
import logging

from core import pad, runtime_types
from core.node import Node, NodeMetadata


class AutoConvert(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Automatically converts data between compatible types"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="utility", tags=["auto", "type"])

    async def resolve_pads(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad("sink"))
        if not sink:
            sink = pad.StatelessSinkPad(
                id="sink",
                owner_node=self,
                group="sink",
                type_constraints=None,
            )
            self.pads.append(sink)

        source = cast(pad.StatelessSourcePad, self.get_pad("source"))
        if not source:
            source = pad.StatelessSourcePad(
                id="source",
                owner_node=self,
                group="source",
                type_constraints=None,
            )
            self.pads.append(source)
        prev_pad = sink.get_previous_pad()
        if prev_pad:
            sink.set_type_constraints(prev_pad.get_type_constraints())

        if source.get_next_pads():
            tcs = None
            for np in source.get_next_pads():
                np_tcs = np.get_type_constraints()
                tcs = pad.types.INTERSECTION(tcs, np_tcs)
            source.set_type_constraints(tcs)

    async def run(self):
        sink = cast(pad.StatelessSinkPad, self.get_pad_required("sink"))
        source = cast(pad.StatelessSourcePad, self.get_pad_required("source"))
        sink_tcs = sink.get_type_constraints()
        sink_type = sink_tcs[0] if sink_tcs else None
        source_tcs = source.get_type_constraints()
        source_type = source_tcs[0] if source_tcs else None
        async for item in sink:
            if not sink_type or not source_type:
                continue

            sink_type = cast(pad.types.PadType, sink_type)
            source_type = cast(pad.types.PadType, source_type)
            if isinstance(source_type, pad.types.Trigger):
                source.push_item(runtime_types.Trigger(), item.ctx)
            elif isinstance(source_type, pad.types.Audio):
                if isinstance(item.value, runtime_types.AudioFrame):
                    source.push_item(item.value, item.ctx)
                elif isinstance(item.value, runtime_types.AudioClip):
                    for af in item.value.audio:
                        source.push_item(af, item.ctx)
            elif isinstance(source_type, pad.types.String):
                if isinstance(item.value, str):
                    source.push_item(item.value, item.ctx)
                elif isinstance(item.value, float):
                    source.push_item(str(item.value), item.ctx)
                elif isinstance(item.value, int):
                    source.push_item(str(item.value), item.ctx)
                elif isinstance(item.value, runtime_types.ContextMessage):
                    txt: str | None = None
                    for cnt in item.value.content:
                        if isinstance(
                            cnt, runtime_types.ContextMessageContentItem_Text
                        ):
                            txt = cnt.content
                            break
                        elif isinstance(
                            cnt, runtime_types.ContextMessageContentItem_Audio
                        ):
                            if cnt.clip.transcription:
                                txt = cnt.clip.transcription
                            break
                    if txt is not None:
                        source.push_item(txt, item.ctx)
                elif isinstance(source_type, bool):
                    if isinstance(item.value, bool):
                        source.push_item(str(item.value), item.ctx)
                elif isinstance(item.value, dict):
                    try:
                        json_str = json.dumps(item.value)
                        source.push_item(json_str, item.ctx)
                    except TypeError:
                        source.push_item(
                            f"Cannot convert {item.value} to string", item.ctx
                        )

            item.ctx.complete()
