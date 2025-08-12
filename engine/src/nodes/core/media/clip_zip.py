# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import cast

from core import pad, runtime_types
from core.node import Node, NodeMetadata


class ClipZip(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Combines audio and video clips into a single av clip."

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="media", tags=["control", "clip", "zip"]
        )

    async def resolve_pads(self):
        video_clip = cast(pad.StatelessSinkPad, self.get_pad("video_clip"))
        if not video_clip:
            self.pads.append(
                pad.StatelessSinkPad(
                    id="video_clip",
                    owner_node=self,
                    type_constraints=[pad.types.VideoClip()],
                    group="video_clip",
                )
            )
            video_clip = cast(pad.StatelessSinkPad, self.get_pad("video_clip"))

        audio_clip = cast(pad.StatelessSinkPad, self.get_pad("audio_clip"))
        if not audio_clip:
            self.pads.append(
                pad.StatelessSinkPad(
                    id="audio_clip",
                    owner_node=self,
                    type_constraints=[pad.types.AudioClip()],
                    group="audio_clip",
                )
            )
            audio_clip = cast(pad.StatelessSinkPad, self.get_pad("audio_clip"))

        av_clip = cast(pad.StatelessSourcePad, self.get_pad("av_clip"))
        if not av_clip:
            self.pads.append(
                pad.StatelessSourcePad(
                    id="av_clip",
                    owner_node=self,
                    type_constraints=[pad.types.AVClip()],
                    group="av_clip",
                )
            )
            av_clip = cast(pad.StatelessSourcePad, self.get_pad("av_clip"))

    async def run(self):
        video_clip = cast(pad.StatelessSinkPad, self.get_pad_required("video_clip"))
        audio_clip = cast(pad.StatelessSinkPad, self.get_pad_required("audio_clip"))
        av_clip = cast(pad.StatelessSourcePad, self.get_pad_required("av_clip"))

        has_video = video_clip.get_previous_pad() is not None
        has_audio = audio_clip.get_previous_pad() is not None

        current_video_clip: runtime_types.VideoClip | None = None
        video_ctx: pad.RequestContext | None = None

        current_audio_clip: runtime_types.AudioClip | None = None
        audio_ctx: pad.RequestContext | None = None

        def send_av_clip():
            nonlocal current_video_clip, current_audio_clip, video_ctx, audio_ctx
            if has_audio and has_video:
                if not current_video_clip or not current_audio_clip:
                    return

                if not video_ctx or not audio_ctx:
                    return

                clip = runtime_types.AVClip(
                    video=current_video_clip, audio=current_audio_clip
                )
                ac = cast(pad.RequestContext, audio_ctx)
                video_ctx.add_done_callback(lambda _: ac.complete())
                av_clip.push_item(clip, video_ctx)
                video_ctx.complete()
                current_video_clip = None
                current_audio_clip = None
                audio_ctx = None
                video_ctx = None
            elif has_audio and not has_video:
                if not current_audio_clip or not audio_ctx:
                    return

                clip = runtime_types.AVClip(
                    audio=current_audio_clip, video=runtime_types.VideoClip(video=[])
                )
                ac = cast(pad.RequestContext, audio_ctx)
                av_clip.push_item(clip, ac)
                ac.complete()
                current_audio_clip = None
                audio_ctx = None
            elif has_video and not has_audio:
                if not current_video_clip or not video_ctx:
                    return

                clip = runtime_types.AVClip(
                    video=current_video_clip, audio=runtime_types.AudioClip(audio=[])
                )
                vc = cast(pad.RequestContext, video_ctx)
                av_clip.push_item(clip, vc)
                vc.complete()
                current_video_clip = None
                video_ctx = None

        async def video_task():
            nonlocal current_video_clip, video_ctx
            async for item in video_clip:
                current_video_clip = item.value
                video_ctx = item.ctx
                send_av_clip()

        async def audio_task():
            nonlocal current_audio_clip, audio_ctx
            async for item in audio_clip:
                current_audio_clip = item.value
                audio_ctx = item.ctx
                send_av_clip()

        await asyncio.gather(video_task(), audio_task())
