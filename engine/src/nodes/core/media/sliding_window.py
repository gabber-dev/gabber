# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

from core import runtime_types
from core.node import Node, NodeMetadata
from core.pad import PropertySinkPad, StatelessSinkPad, StatelessSourcePad, types


class SlidingWindow(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Slides a window of media and writes based on input trigger."

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="media", tags=["control", "sliding_window"]
        )

    async def resolve_pads(self):
        video_sink = cast(StatelessSinkPad, self.get_pad("video"))
        if not video_sink:
            self.pads.append(
                StatelessSinkPad(
                    id="video",
                    owner_node=self,
                    type_constraints=[types.Video()],
                    group="video",
                )
            )
            video_sink = cast(StatelessSinkPad, self.get_pad("video"))

        audio_sink = cast(StatelessSinkPad, self.get_pad("audio"))
        if not audio_sink:
            self.pads.append(
                StatelessSinkPad(
                    id="audio",
                    owner_node=self,
                    type_constraints=[types.Audio()],
                    group="audio",
                )
            )
            audio_sink = cast(StatelessSinkPad, self.get_pad("audio"))

        flush_trigger = cast(StatelessSinkPad, self.get_pad("flush"))
        if not flush_trigger:
            self.pads.append(
                StatelessSinkPad(
                    id="flush",
                    owner_node=self,
                    type_constraints=[types.Trigger()],
                    group="flush",
                )
            )
            flush_trigger = cast(StatelessSinkPad, self.get_pad("flush"))

        reset = cast(StatelessSinkPad, self.get_pad("reset"))
        if not reset:
            self.pads.append(
                StatelessSinkPad(
                    id="reset",
                    owner_node=self,
                    type_constraints=[types.Trigger()],
                    group="reset",
                )
            )
            reset = cast(StatelessSinkPad, self.get_pad("reset"))

        clip_source = cast(StatelessSourcePad, self.get_pad("clip"))
        if not clip_source:
            self.pads.append(
                StatelessSourcePad(
                    id="clip",
                    owner_node=self,
                    type_constraints=[
                        types.VideoClip(),
                        types.AudioClip(),
                        types.AVClip(),
                    ],
                    group="clip",
                )
            )
            clip_source = cast(StatelessSourcePad, self.get_pad("clip"))

        window_size_sink = cast(PropertySinkPad, self.get_pad("window_size_s"))
        if not window_size_sink:
            self.pads.append(
                PropertySinkPad(
                    id="window_size_s",
                    owner_node=self,
                    default_type_constraints=[types.Float()],
                    group="window_size_s",
                    value=5.0,
                )
            )
            window_size_sink = cast(PropertySinkPad, self.get_pad("window_size_s"))

        self._resolve_types()

    def _resolve_types(self):
        video_sink = cast(StatelessSinkPad, self.get_pad_required("video"))
        audio_sink = cast(StatelessSinkPad, self.get_pad_required("audio"))
        clip_source = cast(StatelessSourcePad, self.get_pad_required("clip"))

        if (
            video_sink.get_previous_pad() is not None
            and audio_sink.get_previous_pad() is not None
        ):
            clip_source.set_type_constraints([types.AVClip()])
            return

        if (
            video_sink.get_previous_pad() is not None
            and audio_sink.get_previous_pad() is None
        ):
            clip_source.set_type_constraints([types.VideoClip()])
            return

        if (
            audio_sink.get_previous_pad() is not None
            and video_sink.get_previous_pad() is None
        ):
            clip_source.set_type_constraints([types.AudioClip()])
            return

        clip_source.set_type_constraints(
            [types.VideoClip(), types.AudioClip(), types.AVClip()]
        )

    async def run(self):
        clip_pad = cast(StatelessSourcePad, self.get_pad_required("clip"))
        audio_sink = cast(StatelessSinkPad, self.get_pad_required("audio"))
        video_sink = cast(StatelessSinkPad, self.get_pad_required("video"))
        flush = cast(StatelessSinkPad, self.get_pad_required("flush"))
        reset = cast(StatelessSinkPad, self.get_pad_required("reset"))
        window = cast(PropertySinkPad, self.get_pad_required("window_size_s"))
        audio_frames: list[runtime_types.AudioFrame] = []
        video_frames: list[runtime_types.VideoFrame] = []

        def slide_audio():
            window_size = cast(float, window.get_value())

            duration = sum([item.original_data.duration for item in audio_frames])
            while duration > window_size:
                item = audio_frames.pop(0)
                duration -= item.original_data.duration

        def slide_video():
            window_size = cast(float, window.get_value())

            if len(video_frames) < 2:
                return

            duration = video_frames[-1].timestamp - video_frames[0].timestamp

            while duration > window_size and len(video_frames) > 1:
                video_frames.pop(0)
                duration = video_frames[-1].timestamp - video_frames[0].timestamp

        async def audio_task():
            async for item in audio_sink:
                audio_frames.append(item.value)
                item.ctx.complete()
                slide_audio()

        async def video_task():
            async for item in video_sink:
                video_frames.append(item.value)
                item.ctx.complete()
                slide_video()

        async def flush_task():
            async for item in flush:
                tcs = clip_pad.get_type_constraints()
                if not tcs or len(tcs) != 1:
                    continue

                if tcs[0] == types.VideoClip():
                    vc = runtime_types.VideoClip(video_frames[:])
                    clip_pad.push_item(vc, item.ctx)
                elif tcs[0] == types.AudioClip():
                    ac = runtime_types.AudioClip(audio_frames[:])
                    clip_pad.push_item(ac, item.ctx)
                elif tcs[0] == types.AVClip():
                    vc = runtime_types.VideoClip(video_frames[:])
                    ac = runtime_types.AudioClip(audio_frames[:])
                    clip = runtime_types.AVClip(video=vc, audio=ac)
                    clip_pad.push_item(clip, item.ctx)

                item.ctx.complete()

                audio_frames.clear()
                video_frames.clear()

        async def reset_task():
            async for item in reset:
                audio_frames.clear()
                video_frames.clear()

        asyncio.gather(audio_task(), video_task(), flush_task(), reset_task())
