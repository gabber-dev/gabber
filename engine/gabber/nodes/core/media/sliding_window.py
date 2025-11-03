# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

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
        
        # Track frame arrival times to estimate FPS dynamically
        import time
        video_frame_arrival_times: list[float] = []

        def slide_audio():
            window_size = cast(float, window.get_value())

            duration = sum([item.original_data.duration for item in audio_frames])
            while duration > window_size:
                item = audio_frames.pop(0)
                duration -= item.original_data.duration

        def slide_video():
            nonlocal video_frame_arrival_times
            window_size = cast(float, window.get_value())

            if len(video_frames) < 2:
                return

            # Slide based on timestamp duration
            duration = video_frames[-1].timestamp - video_frames[0].timestamp
            while duration > window_size and len(video_frames) > 1:
                video_frames.pop(0)
                video_frame_arrival_times.pop(0)
                if len(video_frames) >= 2:
                    duration = video_frames[-1].timestamp - video_frames[0].timestamp
                else:
                    break

        async def audio_task():
            async for item in audio_sink:
                audio_frames.append(item.value)
                item.ctx.complete()
                slide_audio()

        async def video_task():
            nonlocal video_frame_arrival_times
            async for item in video_sink:
                video_frames.append(item.value)
                video_frame_arrival_times.append(time.time())
                item.ctx.complete()
                slide_video()

        async def flush_task():
            nonlocal video_frame_arrival_times
            async for item in flush:
                tcs = clip_pad.get_type_constraints()
                if not tcs or len(tcs) != 1:
                    continue

                window_size = cast(float, window.get_value())

                # Limit video frames based on estimated FPS from actual arrival times
                frames_to_flush = video_frames[:]
                if len(video_frame_arrival_times) >= 2 and len(frames_to_flush) > 0:
                    # Calculate actual FPS from wall-clock arrival times
                    arrival_duration = video_frame_arrival_times[-1] - video_frame_arrival_times[0]
                    if arrival_duration > 0:
                        estimated_fps = (len(video_frame_arrival_times) - 1) / arrival_duration
                        expected_frame_count = int(window_size * estimated_fps)
                        
                        # Take the most recent expected_frame_count frames
                        # This ensures consistent frame counts based on actual arrival rate
                        if expected_frame_count > 0 and len(frames_to_flush) > expected_frame_count:
                            frames_to_flush = frames_to_flush[-expected_frame_count:]

                if tcs[0] == pad_constraints.VideoClip():
                    vc = runtime.VideoClip(frames_to_flush)
                    clip_pad.push_item(vc, item.ctx)
                elif tcs[0] == pad_constraints.AudioClip():
                    ac = runtime.AudioClip(audio_frames[:])
                    clip_pad.push_item(ac, item.ctx)
                elif tcs[0] == pad_constraints.AVClip():
                    vc = runtime.VideoClip(frames_to_flush)
                    ac = runtime.AudioClip(audio_frames[:])
                    clip = runtime.AVClip(video=vc, audio=ac)
                    clip_pad.push_item(clip, item.ctx)

                item.ctx.complete()

                audio_frames.clear()
                video_frames.clear()
                video_frame_arrival_times.clear()

        async def reset_task():
            nonlocal video_frame_arrival_times
            async for item in reset:
                audio_frames.clear()
                video_frames.clear()
                video_frame_arrival_times.clear()

        await asyncio.gather(audio_task(), video_task(), flush_task(), reset_task())
