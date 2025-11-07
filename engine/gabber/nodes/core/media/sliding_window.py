# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast
import time

from gabber.core.types import runtime, pad_constraints
from gabber.core.node import Node, NodeMetadata
from gabber.core.pad import PropertySinkPad, StatelessSinkPad, StatelessSourcePad


class SlidingWindow(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Slides a window of media and writes based on input trigger."

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="media", tags=["control", "sliding_window"]
        )

    def resolve_pads(self):
        video_sink = cast(StatelessSinkPad, self.get_pad("video"))
        if not video_sink:
            video_sink = StatelessSinkPad(
                id="video",
                owner_node=self,
                default_type_constraints=[pad_constraints.Video()],
                group="video",
            )

        audio_sink = cast(StatelessSinkPad, self.get_pad("audio"))
        if not audio_sink:
            audio_sink = StatelessSinkPad(
                id="audio",
                owner_node=self,
                default_type_constraints=[pad_constraints.Audio()],
                group="audio",
            )

        flush_trigger = cast(StatelessSinkPad, self.get_pad("flush"))
        if not flush_trigger:
            flush_trigger = StatelessSinkPad(
                id="flush",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
                group="flush",
            )

        reset = cast(StatelessSinkPad, self.get_pad("reset"))
        if not reset:
            reset = StatelessSinkPad(
                id="reset",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
                group="reset",
            )

        clip_source = cast(StatelessSourcePad, self.get_pad("clip"))
        if not clip_source:
            clip_source = StatelessSourcePad(
                id="clip",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.VideoClip(),
                    pad_constraints.AudioClip(),
                    pad_constraints.AVClip(),
                ],
                group="clip",
            )

        window_size_sink = cast(PropertySinkPad, self.get_pad("window_size_s"))
        if not window_size_sink:
            window_size_sink = PropertySinkPad(
                id="window_size_s",
                owner_node=self,
                default_type_constraints=[pad_constraints.Float()],
                group="window_size_s",
                value=5.0,
            )

        self.pads = [
            video_sink,
            audio_sink,
            flush_trigger,
            reset,
            clip_source,
            window_size_sink,
        ]

        self._resolve_types()

    def _resolve_types(self):
        video_sink = cast(StatelessSinkPad, self.get_pad_required("video"))
        audio_sink = cast(StatelessSinkPad, self.get_pad_required("audio"))
        clip_source = cast(StatelessSourcePad, self.get_pad_required("clip"))

        if (
            video_sink.get_previous_pad() is not None
            and audio_sink.get_previous_pad() is not None
        ):
            clip_source.set_default_type_constraints([pad_constraints.AVClip()])
            return

        if (
            video_sink.get_previous_pad() is not None
            and audio_sink.get_previous_pad() is None
        ):
            clip_source.set_default_type_constraints([pad_constraints.VideoClip()])
            return

        if (
            audio_sink.get_previous_pad() is not None
            and video_sink.get_previous_pad() is None
        ):
            clip_source.set_default_type_constraints([pad_constraints.AudioClip()])
            return

        clip_source.set_default_type_constraints(
            [
                pad_constraints.VideoClip(),
                pad_constraints.AudioClip(),
                pad_constraints.AVClip(),
            ]
        )

    async def run(self):
        clip_pad = cast(StatelessSourcePad, self.get_pad_required("clip"))
        audio_sink = cast(StatelessSinkPad, self.get_pad_required("audio"))
        video_sink = cast(StatelessSinkPad, self.get_pad_required("video"))
        flush = cast(StatelessSinkPad, self.get_pad_required("flush"))
        reset = cast(StatelessSinkPad, self.get_pad_required("reset"))
        window = cast(PropertySinkPad, self.get_pad_required("window_size_s"))
        audio_frames: list[runtime.AudioFrame] = []
        video_frames: list[runtime.VideoFrame] = []

        frame_arrivals: list[
            tuple[runtime.VideoFrame, float]
        ] = []  # (frame, arrival_time)

        def slide_audio():
            window_size = cast(float, window.get_value())

            duration = sum([item.original_data.duration for item in audio_frames])
            while duration > window_size:
                item = audio_frames.pop(0)
                duration -= item.original_data.duration

        def slide_video():
            nonlocal frame_arrivals
            window_size = cast(float, window.get_value())
            current_time = time.time()

            while (
                frame_arrivals and (current_time - frame_arrivals[0][1]) > window_size
            ):
                frame_arrivals.pop(0)

            video_frames.clear()
            video_frames.extend([frame for frame, _ in frame_arrivals])

        async def audio_task():
            async for item in audio_sink:
                audio_frames.append(item.value)
                item.ctx.complete()
                slide_audio()

        async def video_task():
            nonlocal frame_arrivals
            async for item in video_sink:
                arrival_time = time.time()
                frame_arrivals.append((item.value, arrival_time))
                item.ctx.complete()
                slide_video()

        async def flush_task():
            async for item in flush:
                tcs = clip_pad.get_type_constraints()
                if not tcs or len(tcs) != 1:
                    continue

                if tcs[0] == pad_constraints.VideoClip():
                    vc = runtime.VideoClip(video_frames[:])
                    clip_pad.push_item(vc, item.ctx)
                elif tcs[0] == pad_constraints.AudioClip():
                    ac = runtime.AudioClip(audio_frames[:])
                    clip_pad.push_item(ac, item.ctx)
                elif tcs[0] == pad_constraints.AVClip():
                    vc = runtime.VideoClip(video_frames[:])
                    ac = runtime.AudioClip(audio_frames[:])
                    clip = runtime.AVClip(video=vc, audio=ac)
                    clip_pad.push_item(clip, item.ctx)

                item.ctx.complete()

                audio_frames.clear()
                video_frames.clear()
                frame_arrivals.clear()

        async def reset_task():
            nonlocal frame_arrivals
            async for item in reset:
                audio_frames.clear()
                video_frames.clear()
                frame_arrivals.clear()

        await asyncio.gather(audio_task(), video_task(), flush_task(), reset_task())
