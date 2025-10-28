# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

import numpy as np
from gabber.core import pad
from gabber.core.node import Node
from gabber.core.types import runtime
from livekit import rtc
from gabber.core.node import NodeMetadata, NodeNote
from gabber.core.types import pad_constraints


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
        audio = self.get_stateless_sink_pad(runtime.AudioFrame, "audio")
        if not audio:
            audio = pad.StatelessSinkPad(
                id="audio",
                owner_node=self,
                default_type_constraints=[pad_constraints.Audio()],
                group="audio",
            )
        video = self.get_stateless_sink_pad(runtime.VideoFrame, "video")
        if not video:
            video = pad.StatelessSinkPad(
                id="video",
                owner_node=self,
                default_type_constraints=[pad_constraints.Video()],
                group="video",
            )

        self.pads = [audio, video]

    def get_notes(self) -> list[NodeNote]:
        audio_pad = self.get_stateless_sink_pad_required(runtime.AudioFrame, "audio")
        video_pad = self.get_stateless_sink_pad_required(runtime.VideoFrame, "video")
        notes: list[NodeNote] = []
        any_connections = False

        if audio_pad and audio_pad.get_previous_pad():
            any_connections = True

        if video_pad and video_pad.get_previous_pad():
            any_connections = True

        if not any_connections:
            notes.extend(
                [
                    NodeNote(
                        level="warning",
                        message="Output node has no connected pads. No media will be sent to the user.",
                        pad="audio",
                    ),
                    NodeNote(
                        level="warning",
                        message="Output node has no connected pads. No media will be sent to the user.",
                        pad="video",
                    ),
                ]
            )

        return notes

    async def run(self):
        audio = self.get_stateless_sink_pad_required(runtime.AudioFrame, "audio")
        video = self.get_stateless_sink_pad_required(runtime.VideoFrame, "video")

        async def audio_consume():
            source = rtc.AudioSource(24000, 1)
            track = rtc.LocalAudioTrack.create_audio_track(f"{self.id}:audio", source)
            options = rtc.TrackPublishOptions()
            options.source = rtc.TrackSource.SOURCE_MICROPHONE
            await self.room.local_participant.publish_track(track, options)

            async for item in audio:
                a_frame = item.value
                rtc_frame = rtc.AudioFrame.create(
                    24000, 1, a_frame.data_24000hz.sample_count
                )
                dst = np.frombuffer(rtc_frame.data, dtype=np.int16)
                np.copyto(dst, a_frame.data_24000hz.data[:])
                await source.capture_frame(rtc_frame)
                item.ctx.complete()

        async def video_consume():
            source = rtc.VideoSource(width=640, height=480)
            track = rtc.LocalVideoTrack.create_video_track(f"{self.id}:video", source)
            options = rtc.TrackPublishOptions()
            options.source = rtc.TrackSource.SOURCE_CAMERA
            options.video_encoding.max_bitrate = 4_000_000
            options.video_encoding.max_framerate = 24
            await self.room.local_participant.publish_track(track, options)
            async for f in video:
                v_frame = f.value
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
