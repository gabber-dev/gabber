# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from gabber.core import node, pad
from gabber.core.types import runtime, pad_constraints
from gabber.core.node import NodeMetadata
from gabber.lib import stt


class LocalViseme(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Gabber Speech-to-Text. This node requires running the local gabber stt server. See `services/gabber-stt` for more details."

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="ai",
            secondary="local",
            tags=["stt", "speech", "viseme"],
        )

    def resolve_pads(self):
        audio_sink = cast(pad.StatelessSinkPad, self.get_pad("audio"))
        if audio_sink is None:
            audio_sink = pad.StatelessSinkPad(
                id="audio",
                group="audio",
                owner_node=self,
                default_type_constraints=[pad_constraints.Audio()],
            )

        port = cast(pad.PropertySinkPad, self.get_pad("port"))
        if port is None:
            port = pad.PropertySinkPad(
                id="port",
                group="port",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer()],
                value=7004,
            )

        viseme = cast(pad.StatelessSourcePad, self.get_pad("viseme"))
        if viseme is None:
            viseme = pad.StatelessSourcePad(
                id="viseme",
                group="viseme",
                owner_node=self,
                default_type_constraints=[pad_constraints.Viseme()],
            )

        self.pads = [
            audio_sink,
            port,
            viseme,
        ]

    def get_url(self):
        port_pad = cast(pad.PropertySinkPad, self.get_pad_required("port"))
        port = port_pad.get_value()
        return f"ws://localhost:{port}"

    async def run(self):
        audio_sink = cast(pad.StatelessSinkPad, self.get_pad_required("audio"))
        audio_sink = self.get_stateless_sink_pad_required(runtime.AudioFrame, "audio")
        viseme = self.get_stateless_source_pad_required(runtime.Viseme, "viseme")

        url = self.get_url()

        stt_impl = stt.Gabber(logger=self.logger, url=url, viseme_mode=True)

        stt_run_t = asyncio.create_task(stt_impl.run())

        async def audio_sink_task() -> None:
            async for audio in audio_sink:
                stt_impl.push_audio(audio.value)
                audio.ctx.complete()

        async def stt_event_task() -> None:
            ctx: pad.RequestContext | None = None
            async for event in stt_impl:
                if isinstance(event, stt.STTEvent_Viseme):
                    ctx = pad.RequestContext(parent=None, publisher_metadata=None)
                    visem_val = runtime.VisemeEnum.SILENCE
                    try:
                        visem_val = runtime.VisemeEnum(event.viseme)
                    except ValueError:
                        self.logger.warning(
                            f"Unknown viseme value received: {event.viseme}"
                        )
                    viseme.push_item(runtime.Viseme(value=visem_val), ctx)
                    ctx.complete()

        audio_sink_t = asyncio.create_task(audio_sink_task())
        event_t = asyncio.create_task(stt_event_task())

        try:
            await asyncio.gather(stt_run_t, audio_sink_t, event_t)
        except asyncio.CancelledError:
            pass
        finally:
            stt_impl.close()
            audio_sink_t.cancel()
