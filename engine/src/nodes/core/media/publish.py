# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

import numpy as np
from core import node, pad
from core.node import NodeMetadata
from core.runtime_types import AudioFrame, AudioFrameData, VideoFrame
from lib.audio import Resampler
from livekit import rtc
from utils import audio_stream_provider, video_stream_provider


class Publish(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Stream audio and video into your Gabber flow"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="core", secondary="media", tags=["input", "stream"])

    async def resolve_pads(self):
        audio_source = cast(pad.StatelessSourcePad, self.get_pad("audio"))

        if not audio_source:
            self.pads.append(
                pad.StatelessSourcePad(
                    id="audio",
                    owner_node=self,
                    group="audio",
                    type_constraints=[pad.types.Audio()],
                )
            )

        video_source = cast(pad.StatelessSourcePad, self.get_pad("video"))
        if not video_source:
            self.pads.append(
                pad.StatelessSourcePad(
                    id="video",
                    owner_node=self,
                    group="video",
                    type_constraints=[pad.types.Video()],
                )
            )

    async def run(self):
        audio_source = cast(pad.StatelessSourcePad, self.get_pad_required("audio"))
        video_source = cast(pad.StatelessSourcePad, self.get_pad_required("video"))

        resampler_16000hz = Resampler(16000)
        resampler_24000hz = Resampler(24000)
        resampler_44100hz = Resampler(44100)
        resampler_48000hz = Resampler(48000)

        async def video_consume():
            while True:
                video_stream = await video_stream_provider(
                    self.room, f"{self.id}:video"
                )
                async for frame in video_stream:
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
            while True:
                audio_stream = await audio_stream_provider(
                    self.room, f"{self.id}:audio"
                )
                async for frame in audio_stream:
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

        await asyncio.gather(
            video_consume(),
            audio_consume(),
        )
