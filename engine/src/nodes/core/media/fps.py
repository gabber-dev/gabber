# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import time
from typing import cast

from core import pad
from core.node import Node, NodeMetadata
from core.pad import PropertySinkPad, StatelessSinkPad, StatelessSourcePad, types
from core.runtime_types import VideoFrame


class FPS(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Controls the frame rate of the video being processed"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="media", tags=["control", "fps"])

    async def resolve_pads(self):
        sink = cast(StatelessSinkPad, self.get_pad("video_in"))
        if not sink:
            sink = StatelessSinkPad(
                id="video_in",
                owner_node=self,
                type_constraints=[types.Video()],
                group="video_in",
            )

        source = cast(StatelessSourcePad, self.get_pad("video_out"))
        if not source:
            source = StatelessSourcePad(
                id="video_out",
                owner_node=self,
                type_constraints=[types.Video()],
                group="video_out",
            )

        fps_sink = cast(PropertySinkPad, self.get_pad("fps"))
        if not fps_sink:
            fps_sink = PropertySinkPad(
                id="fps",
                owner_node=self,
                type_constraints=[types.Float(minimum=0.0, maximum=30.0)],
                group="fps",
                value=0.5,
            )

        self.pads = [sink, source, fps_sink]

    async def run(self):
        sink = cast(StatelessSinkPad, self.get_pad_required("video_in"))
        fps_pad = cast(PropertySinkPad, self.get_pad_required("fps"))
        source = cast(StatelessSourcePad, self.get_pad_required("video_out"))

        last_frame: VideoFrame | None = None
        last_ctx = pad.RequestContext(parent=None)

        async def sink_task():
            nonlocal last_frame, last_ctx
            async for frame in sink:
                if last_ctx is not None:
                    last_ctx.complete()
                last_frame = frame.value
                last_ctx = frame.ctx

        async def source_task():
            nonlocal last_frame
            last_send_time = time.time()
            while True:
                fps = fps_pad.get_value()
                if fps <= 0:
                    await asyncio.sleep(1.0)
                    continue

                now = time.time()
                if now >= last_send_time + 1.0 / fps and last_frame is not None:
                    last_send_time = now
                    source.push_item(last_frame, last_ctx)
                    last_ctx.complete()
                    await asyncio.sleep(0.01)
                else:
                    sleep_time = max(0.01, last_send_time + 1.0 / fps - now)
                    await asyncio.sleep(sleep_time)
                    continue

        await asyncio.gather(sink_task(), source_task())
