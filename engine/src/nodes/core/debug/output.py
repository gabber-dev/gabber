# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

import numpy as np
from core import pad
from core.node import Node
from core.runtime_types import AudioFrame, VideoFrame
from livekit import rtc
from core.node import NodeMetadata


class Output(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Outputs audio and video to the end user"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="media", tags=["output", "display"]
        )

    def resolve_pads(self):
        audio = cast(pad.StatelessSinkPad, self.get_pad("audio_sink"))
        if not audio:
            audio = pad.StatelessSinkPad(
                    id="audio",
                    owner_node=self,
                    default_type_constraints=[pad.types.Audio()],
                    group="audio",
                )
        video = cast(pad.StatelessSinkPad, self.get_pad("video_sink"))
        if not video:
            video = pad.StatelessSinkPad(
                    id="video",
                    owner_node=self,
                    default_type_constraints=[pad.types.Video()],
                    group="video",
                )

        self.pads = [audio, video]

    async def run(self):
        audio = cast(pad.StatelessSinkPad, self.get_pad_required("audio"))
        video = cast(pad.StatelessSinkPad, self.get_pad_required("video"))

        async def audio_consume():
            source = rtc.AudioSource(24000, 1)
            track = rtc.LocalAudioTrack.create_audio_track(f"{self.id}:audio", source)
            options = rtc.TrackPublishOptions()
            options.source = rtc.TrackSource.SOURCE_MICROPHONE
            await self.room.local_participant.publish_track(track, options)

            async for f in audio:
                a_frame = cast(AudioFrame, f.value)
                rtc_frame = rtc.AudioFrame.create(
                    24000, 1, a_frame.data_24000hz.sample_count
                )
                dst = np.frombuffer(rtc_frame.data, dtype=np.int16)
                np.copyto(dst, a_frame.data_24000hz.data[:])
                await source.capture_frame(rtc_frame)
                f.ctx.complete()

        async def video_consume():
            source = rtc.VideoSource(width=640, height=480)
            track = rtc.LocalVideoTrack.create_video_track(f"{self.id}:video", source)
            options = rtc.TrackPublishOptions()
            options.source = rtc.TrackSource.SOURCE_CAMERA
            await self.room.local_participant.publish_track(track, options)
            async for f in video:
                v_frame = cast(VideoFrame, f.value)
                frame = rtc.VideoFrame(
                    v_frame.width,
                    v_frame.height,
                    rtc.VideoBufferType.RGBA,
                    v_frame.data.tobytes(),
                )
                source.capture_frame(frame)
                f.ctx.complete()

        try:
            await asyncio.gather(audio_consume(), video_consume())
        except Exception as e:
            print(f"Error in OutputNode: {e}")
