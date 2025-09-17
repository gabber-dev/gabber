# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast
import time

import numpy as np
from gabber.core import node, pad
from gabber.core.node import NodeMetadata
from gabber.core.runtime_types import AudioFrame, AudioFrameData, VideoFrame
from gabber.lib.audio import Resampler
from livekit import rtc
from gabber.utils import audio_stream_provider, video_stream_provider


class Publish(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Stream audio and video into your Gabber flow"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="media", tags=["input", "stream"])

    def resolve_pads(self):
        audio_source = cast(pad.StatelessSourcePad, self.get_pad("audio"))
        if not audio_source:
            audio_source = pad.StatelessSourcePad(
                id="audio",
                owner_node=self,
                group="audio",
                default_type_constraints=[pad.types.Audio()],
            )

        audio_enabled = cast(pad.PropertySourcePad, self.get_pad("audio_enabled"))
        if not audio_enabled:
            audio_enabled = pad.PropertySourcePad(
                id="audio_enabled",
                owner_node=self,
                group="audio_enabled",
                default_type_constraints=[pad.types.Boolean()],
                value=False,
            )

        video_source = cast(pad.StatelessSourcePad, self.get_pad("video"))
        if not video_source:
            video_source = pad.StatelessSourcePad(
                id="video",
                owner_node=self,
                group="video",
                default_type_constraints=[pad.types.Video()],
            )

        video_enabled = cast(pad.PropertySourcePad, self.get_pad("video_enabled"))
        if not video_enabled:
            video_enabled = pad.PropertySourcePad(
                id="video_enabled",
                owner_node=self,
                group="video_enabled",
                default_type_constraints=[pad.types.Boolean()],
                value=False,
            )

        self.pads = [
            audio_source,
            video_source,
            audio_enabled,
            video_enabled,
        ]

    def set_allowed_participant(self, identity: str):
        self._allowed_participant = identity

    def unset_allowed_participant(self, identity: str):
        self._allowed_participant = (
            None if self._allowed_participant == identity else self._allowed_participant
        )
        for rp in self.room.remote_participants.values():
            for track in rp.track_publications.values():
                if (
                    track.name.startswith(f"{self.id}:")
                    and rp.identity != self._allowed_participant
                ):
                    track.set_subscribed(False)

    async def run(self):
        self._allowed_participant: str | None = None
        audio_source = cast(pad.StatelessSourcePad, self.get_pad_required("audio"))
        video_source = cast(pad.StatelessSourcePad, self.get_pad_required("video"))
        audio_enabled = cast(
            pad.PropertySourcePad, self.get_pad_required("audio_enabled")
        )
        video_enabled = cast(
            pad.PropertySourcePad, self.get_pad_required("video_enabled")
        )

        last_audio_frame_time: float | None = None
        last_video_frame_time: float | None = None

        resampler_16000hz = Resampler(16000)
        resampler_24000hz = Resampler(24000)
        resampler_44100hz = Resampler(44100)
        resampler_48000hz = Resampler(48000)

        async def video_consume():
            nonlocal last_video_frame_time
            while True:
                if not self._allowed_participant:
                    await asyncio.sleep(0.5)
                    continue

                video_stream = await video_stream_provider(
                    self.room, f"{self.id}:video", self._allowed_participant
                )

                async for frame in video_stream:
                    last_video_frame_time = time.time()
                    timestamp_s = frame.timestamp_us / 1_000_000.0
                    converted = frame.frame.convert(rtc.VideoBufferType.RGBA)
                    np_buf = np.frombuffer(converted.data, dtype=np.uint8).reshape(
                        frame.frame.height, frame.frame.width, 4
                    )
                    video_frame = VideoFrame(
                        data=np_buf,
                        width=frame.frame.width,
                        height=frame.frame.height,
                        timestamp=timestamp_s,
                    )
                    ctx = pad.RequestContext(parent=None)
                    video_source.push_item(video_frame, ctx)
                    ctx.complete()

        async def audio_consume():
            nonlocal last_audio_frame_time
            while True:
                if not self._allowed_participant:
                    await asyncio.sleep(0.5)
                    continue

                audio_stream = await audio_stream_provider(
                    self.room, f"{self.id}:audio", self._allowed_participant
                )

                async for frame in audio_stream:
                    last_audio_frame_time = time.time()
                    original_data = AudioFrameData(
                        data=np.frombuffer(frame.frame.data, dtype=np.int16).reshape(
                            1, -1
                        ),
                        sample_rate=frame.frame.sample_rate,
                        num_channels=1,
                    )
                    frame_16 = resampler_16000hz.push_audio(original_data)
                    frame_24 = resampler_24000hz.push_audio(original_data)
                    frame_44_1 = resampler_44100hz.push_audio(original_data)
                    frame_48 = resampler_48000hz.push_audio(original_data)

                    frame = AudioFrame(
                        original_data=original_data,
                        data_16000hz=frame_16,
                        data_24000hz=frame_24,
                        data_44100hz=frame_44_1,
                        data_48000hz=frame_48,
                    )

                    ctx = pad.RequestContext(parent=None)
                    audio_source.push_item(frame, ctx)
                    ctx.complete()

        async def frame_timeout():
            while True:
                await asyncio.sleep(0.5)
                current_time = time.time()

                if last_audio_frame_time is None:
                    if audio_enabled.get_value():
                        audio_enabled.push_item(
                            False, pad.RequestContext(parent=None, originator=self.id)
                        )
                else:
                    if current_time - last_audio_frame_time > 1:
                        if audio_enabled.get_value():
                            audio_enabled.push_item(
                                False,
                                pad.RequestContext(parent=None, originator=self.id),
                            )
                    else:
                        if not audio_enabled.get_value():
                            audio_enabled.push_item(
                                True,
                                pad.RequestContext(parent=None, originator=self.id),
                            )
                if last_video_frame_time is None:
                    if video_enabled.get_value():
                        video_enabled.push_item(
                            False, pad.RequestContext(parent=None, originator=self.id)
                        )
                else:
                    if current_time - last_video_frame_time > 1:
                        if video_enabled.get_value():
                            video_enabled.push_item(
                                False,
                                pad.RequestContext(parent=None, originator=self.id),
                            )
                    else:
                        if not video_enabled.get_value():
                            video_enabled.push_item(
                                True,
                                pad.RequestContext(parent=None, originator=self.id),
                            )

        await asyncio.gather(
            video_consume(),
            audio_consume(),
            frame_timeout(),
        )
