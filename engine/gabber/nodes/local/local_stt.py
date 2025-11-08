# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from gabber.core import node, pad
from gabber.core.types import runtime, pad_constraints
from gabber.core.node import NodeMetadata
from gabber.lib import stt


class LocalSTT(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Gabber Speech-to-Text. This node requires running the local gabber stt server. See `services/gabber-stt` for more details."

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="ai",
            secondary="local",
            tags=["stt", "speech"],
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

        speech_clip_source = cast(pad.StatelessSourcePad, self.get_pad("speech_clip"))
        if speech_clip_source is None:
            speech_clip_source = pad.StatelessSourcePad(
                id="speech_clip",
                group="speech_clip",
                owner_node=self,
                default_type_constraints=[pad_constraints.AudioClip()],
            )

        speech_started_source = cast(
            pad.StatelessSourcePad, self.get_pad("speech_started")
        )
        if speech_started_source is None:
            speech_started_source = pad.StatelessSourcePad(
                id="speech_started",
                group="speech_started",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        speech_ended_source = cast(pad.StatelessSourcePad, self.get_pad("speech_ended"))
        if speech_ended_source is None:
            speech_ended_source = pad.StatelessSourcePad(
                id="speech_ended",
                group="speech_ended",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        final_transcription_source = cast(
            pad.StatelessSourcePad, self.get_pad("final_transcription")
        )
        if final_transcription_source is None:
            final_transcription_source = pad.StatelessSourcePad(
                id="final_transcription",
                group="final_transcription",
                owner_node=self,
                default_type_constraints=[pad_constraints.String()],
            )

        is_speaking_source = cast(pad.PropertySourcePad, self.get_pad("is_speaking"))
        if is_speaking_source is None:
            is_speaking_source = pad.PropertySourcePad(
                id="is_speaking",
                group="is_speaking",
                owner_node=self,
                default_type_constraints=[pad_constraints.Boolean()],
                value=False,
            )

        self.pads = [
            audio_sink,
            port,
            speech_clip_source,
            speech_started_source,
            speech_ended_source,
            final_transcription_source,
            is_speaking_source,
        ]

    def get_url(self):
        port_pad = cast(pad.PropertySinkPad, self.get_pad_required("port"))
        port = port_pad.get_value()
        return f"ws://localhost:{port}"

    async def run(self):
        audio_sink = cast(pad.StatelessSinkPad, self.get_pad_required("audio"))
        speech_clip_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("speech_clip")
        )
        speech_started_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("speech_started")
        )
        speech_ended_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("speech_ended")
        )
        final_transcription_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("final_transcription")
        )
        is_speaking_source = cast(
            pad.PropertySourcePad, self.get_pad_required("is_speaking")
        )

        url = self.get_url()

        stt_impl = stt.Gabber(logger=self.logger, url=url)

        stt_run_t = asyncio.create_task(stt_impl.run())

        async def audio_sink_task() -> None:
            async for audio in audio_sink:
                if audio is None:
                    continue
                stt_impl.push_audio(audio.value)
                audio.ctx.complete()

        async def stt_event_task() -> None:
            ctx: pad.RequestContext | None = None
            async for event in stt_impl:
                if isinstance(event, stt.STTEvent_SpeechStarted):
                    ctx = pad.RequestContext(parent=None, publisher_metadata=None)
                    is_speaking_source.push_item(True, ctx)
                    speech_started_source.push_item(runtime.Trigger(), ctx)
                elif isinstance(event, stt.STTEvent_Transcription):
                    # TODO
                    pass
                elif isinstance(event, stt.STTEvent_EndOfTurn):
                    txt = event.clip.transcription
                    if txt is None:
                        txt = ""

                    if ctx is None:
                        logging.error(
                            "Received STTEvent_EndOfTurn without a context. This should not happen."
                        )
                        continue
                    final_transcription_source.push_item(txt, ctx)
                    speech_clip_source.push_item(event.clip, ctx)
                    is_speaking_source.push_item(False, ctx)
                    speech_ended_source.push_item(runtime.Trigger(), ctx)
                    ctx.complete()

        audio_sink_t = asyncio.create_task(audio_sink_task())
        kyutai_event_t = asyncio.create_task(stt_event_task())

        try:
            await asyncio.gather(stt_run_t, audio_sink_t, kyutai_event_t)
        except asyncio.CancelledError:
            pass
        finally:
            stt_impl.close()
            audio_sink_t.cancel()
