# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from core import pad, runtime_types
from core.node import Node, NodeMetadata


class AVClipZip(Node):
    @classmethod
    def get_description(cls) -> str:
        return "Combines audio and video clips into a single av clip."

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="core", secondary="media", tags=["control", "clip", "zip"]
        )

    def resolve_pads(self):
        video_clip = cast(pad.StatelessSinkPad, self.get_pad("video_clip"))
        if not video_clip:
            self.pads.append(
                pad.StatelessSinkPad(
                    id="video_clip",
                    owner_node=self,
                    default_type_constraints=[pad.types.VideoClip()],
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
                    default_type_constraints=[pad.types.AudioClip()],
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
                    default_type_constraints=[pad.types.AVClip()],
                    group="av_clip",
                )
            )
            av_clip = cast(pad.StatelessSourcePad, self.get_pad("av_clip"))

    async def run(self):
        video_clip_pad = cast(pad.StatelessSinkPad, self.get_pad_required("video_clip"))
        audio_clip_pad = cast(pad.StatelessSinkPad, self.get_pad_required("audio_clip"))
        av_clip = cast(pad.StatelessSourcePad, self.get_pad_required("av_clip"))

        connected_pads = [
            p
            for p in [video_clip_pad, audio_clip_pad]
            if p.get_previous_pad() is not None
        ]

        while True:
            try:
                items = await asyncio.gather(*[anext(p) for p in connected_pads])

                video_clip: runtime_types.VideoClip | None = None
                audio_clip: runtime_types.AudioClip | None = None

                for item in items:
                    if isinstance(item.value, runtime_types.VideoClip):
                        video_clip = item.value
                    elif isinstance(item.value, runtime_types.AudioClip):
                        audio_clip = item.value

                if not video_clip:
                    video_clip = runtime_types.VideoClip(video=[])
                if not audio_clip:
                    audio_clip = runtime_types.AudioClip(audio=[])

                res = runtime_types.AVClip(
                    video=video_clip,
                    audio=audio_clip,
                )

                # TODO: propagate context properly
                ctx = cast(pad.RequestContext, pad.RequestContext(parent=None))
                av_clip.push_item(res, ctx)
                for item in items:
                    item.ctx.complete()
                ctx.complete()

            except StopAsyncIteration:
                break
            except Exception as e:
                logging.error("Error while processing AV clips", exc_info=e)
