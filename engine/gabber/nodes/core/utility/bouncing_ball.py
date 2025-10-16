# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast
import time
import numpy as np
from gabber.core import node, pad
from gabber.core.node import NodeMetadata
from gabber.core.types.runtime import AudioFrame, AudioFrameData, VideoFrame
from gabber.lib.audio import Resampler
from gabber.core.types import pad_constraints


class BouncingBall(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Generate synthetic audio and video for testing your Gabber flow"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="media", tags=["input", "stream", "test"]
        )

    def resolve_pads(self):
        audio_source = cast(pad.StatelessSourcePad, self.get_pad("audio"))
        if not audio_source:
            audio_source = pad.StatelessSourcePad(
                id="audio",
                owner_node=self,
                group="audio",
                default_type_constraints=[pad_constraints.Audio()],
            )

        video_source = cast(pad.StatelessSourcePad, self.get_pad("video"))
        if not video_source:
            video_source = pad.StatelessSourcePad(
                id="video",
                owner_node=self,
                group="video",
                default_type_constraints=[pad_constraints.Video()],
            )

        self.pads = [audio_source, video_source]

    async def run(self):
        audio_source = cast(pad.StatelessSourcePad, self.get_pad_required("audio"))
        video_source = cast(pad.StatelessSourcePad, self.get_pad_required("video"))

        last_video_frame_time: float | None = None

        async def play_impact_sound():
            resampler_16000hz = Resampler(16000)
            resampler_24000hz = Resampler(24000)
            resampler_44100hz = Resampler(44100)
            resampler_48000hz = Resampler(48000)
            # Generate impact sound frame (440 Hz tone for dt=0.02s)
            sample_rate = 48000
            dt = 0.02
            num_samples = int(sample_rate * dt)
            freq = 440.0
            amplitude = 0.3 * 32767
            t = np.linspace(0, dt, num_samples, endpoint=False)
            sine = amplitude * np.sin(2 * np.pi * freq * t)
            audio_data_np = np.zeros((1, num_samples), dtype=np.int16)
            audio_data_np[0] = sine.astype(np.int16)
            original_data = AudioFrameData(
                data=audio_data_np,
                sample_rate=sample_rate,
                num_channels=1,
            )
            # Resample
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

        async def video_generate():
            nonlocal last_video_frame_time
            sim_time = 0.0
            dt = 1.0 / 30.0
            width = 640
            height = 480
            x = width / 2.0
            y = height / 2.0
            vx = 200.0  # pixels per second
            vy = 150.0  # pixels per second
            r = 20.0
            colors = [
                (0, 0, 0, 255),
                (255, 0, 0, 255),
                (0, 255, 0, 255),
                (0, 0, 255, 255),
                (255, 255, 0, 255),
                (255, 0, 255, 255),
                (0, 255, 255, 255),
            ]
            bg_idx = 0
            ball_color = np.array([255, 255, 255, 255], dtype=np.uint8)
            while True:
                # Update position
                x += vx * dt
                y += vy * dt
                hit = False
                if x - r < 0 or x + r > width:
                    vx = -vx
                    hit = True
                    x = np.clip(x, r, width - r)
                    self.logger.info("Ball hit vertical wall")
                if y - r < 0 or y + r > height:
                    vy = -vy
                    hit = True
                    y = np.clip(y, r, height - r)
                    self.logger.info("Ball hit horizontal wall")
                if hit:
                    bg_idx = (bg_idx + 1) % len(colors)
                    # Instead of queueing, create a task to generate and push impact sound
                    asyncio.create_task(play_impact_sound())
                # Create buffer
                bg_color = colors[bg_idx]
                buf = np.full((height, width, 4), bg_color, dtype=np.uint8)
                # Draw ball
                yy, xx = np.ogrid[:height, :width]
                mask = (xx - x) ** 2 + (yy - y) ** 2 <= r**2
                for c in range(4):
                    buf[:, :, c][mask] = ball_color[c]
                video_frame = VideoFrame(
                    data=buf,
                    width=width,
                    height=height,
                    timestamp=sim_time,
                )
                ctx = pad.RequestContext(parent=None)
                video_source.push_item(video_frame, ctx)
                ctx.complete()
                last_video_frame_time = time.time()
                sim_time += dt
                await asyncio.sleep(dt)

        await asyncio.gather(video_generate())
