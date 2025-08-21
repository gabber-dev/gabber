# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from core import node, pad, runtime_types
from core.node import NodeMetadata
from lib import stt


class STT(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Speech-to-Text"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="ai",
            secondary="audio",
            tags=["stt", "speech", "kyutai", "assembly", "deepgram"],
        )

    async def resolve_pads(self):
        service = cast(pad.PropertySinkPad, self.get_pad("service"))
        if service is None:
            service = pad.PropertySinkPad(
                id="service",
                group="service",
                owner_node=self,
                type_constraints=[
                    pad.types.Enum(options=["assembly_ai", "local_kyutai", "deepgram"])
                ],
                value="assembly_ai",
            )
            self.pads.append(service)

        audio_sink = cast(pad.StatelessSinkPad, self.get_pad("audio"))
        if audio_sink is None:
            audio_sink = pad.StatelessSinkPad(
                id="audio",
                group="audio",
                owner_node=self,
                type_constraints=[pad.types.Audio()],
            )
            self.pads.append(audio_sink)

        speech_clip_source = cast(pad.StatelessSourcePad, self.get_pad("speech_clip"))
        if speech_clip_source is None:
            speech_clip_source = pad.StatelessSourcePad(
                id="speech_clip",
                group="speech_clip",
                owner_node=self,
                type_constraints=[pad.types.AudioClip()],
            )
            self.pads.append(speech_clip_source)

        speech_started_source = cast(
            pad.StatelessSourcePad, self.get_pad("speech_started")
        )
        if speech_started_source is None:
            speech_started_source = pad.StatelessSourcePad(
                id="speech_started",
                group="speech_started",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(speech_started_source)

        speech_ended_source = cast(pad.StatelessSourcePad, self.get_pad("speech_ended"))
        if speech_ended_source is None:
            speech_ended_source = pad.StatelessSourcePad(
                id="speech_ended",
                group="speech_ended",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(speech_ended_source)

        final_transcription_source = cast(
            pad.StatelessSourcePad, self.get_pad("final_transcription")
        )
        if final_transcription_source is None:
            final_transcription_source = pad.StatelessSourcePad(
                id="final_transcription",
                group="final_transcription",
                owner_node=self,
                type_constraints=[pad.types.String()],
            )
            self.pads.append(final_transcription_source)

        api_key = cast(pad.PropertySinkPad, self.get_pad("api_key"))
        if api_key is None:
            api_key = pad.PropertySinkPad(
                id="api_key",
                group="api_key",
                owner_node=self,
                type_constraints=[pad.types.Secret(options=self.secrets)],
            )
            self.pads.append(api_key)

    async def run(self):
        audio_sink = cast(pad.StatelessSinkPad, self.get_pad_required("audio"))
        service = cast(pad.PropertySinkPad, self.get_pad_required("service"))
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

        stt_impl: stt.STT
        if service.get_value() == "assembly_ai":
            api_key_pad = cast(pad.PropertySinkPad, self.get_pad_required("api_key"))
            api_key_name = api_key_pad.get_value()
            api_key = await self.secret_provider.resolve_secret(api_key_name)
            stt_impl = stt.Assembly(api_key=api_key)
        elif service.get_value() == "local_kyutai":
            stt_impl = stt.Kyutai(port=8080)
        elif service.get_value() == "deepgram":
            api_key_pad = cast(pad.PropertySinkPad, self.get_pad_required("api_key"))
            api_key_name = api_key_pad.get_value()
            api_key = await self.secret_provider.resolve_secret(api_key_name)
            stt_impl = stt.Deepgram(api_key=api_key)
        else:
            logging.error("Unsupported STT service: %s", service.get_value())
            raise ValueError(f"Unsupported STT service: {service.get_value()}")

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
                    ctx = pad.RequestContext(parent=None)
                    speech_started_source.push_item(runtime_types.Trigger(), ctx)
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
                    speech_ended_source.push_item(runtime_types.Trigger(), ctx)
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
