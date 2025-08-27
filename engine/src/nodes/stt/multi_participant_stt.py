# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from core import node, pad, runtime_types
from core.node import NodeMetadata
from lib import stt
from enum import Enum


class MultiParticipantSTT(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "MultiParticipant Speech-to-Text"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="ai",
            secondary="audio",
            tags=["stt", "speech", "kyutai", "assembly", "deepgram"],
        )

    def resolve_pads(self):
        service = cast(pad.PropertySinkPad, self.get_pad("service"))
        if service is None:
            service = pad.PropertySinkPad(
                id="service",
                group="service",
                owner_node=self,
                default_type_constraints=[
                    pad.types.Enum(options=["assembly_ai", "local_kyutai", "deepgram"])
                ],
                value="assembly_ai",
            )

        api_key = cast(pad.PropertySinkPad, self.get_pad("api_key"))
        if api_key is None:
            api_key = pad.PropertySinkPad(
                id="api_key",
                group="api_key",
                owner_node=self,
                default_type_constraints=[pad.types.Secret(options=self.secrets)],
            )

        num_participants = cast(pad.PropertySinkPad, self.get_pad("num_participants"))
        if num_participants is None:
            num_participants = pad.PropertySinkPad(
                id="num_participants",
                group="num_participants",
                owner_node=self,
                default_type_constraints=[pad.types.Integer()],
                value=2,
            )

        audio_sinks: list[pad.StatelessSinkPad] = []
        for i in range(num_participants.get_value() or 1):
            audio_sink = cast(pad.StatelessSinkPad, self.get_pad(f"audio_{i}"))
            if audio_sink is None:
                audio_sink = pad.StatelessSinkPad(
                    id=f"audio_{i}",
                    group="audio",
                    owner_node=self,
                    default_type_constraints=[pad.types.Audio()],
                )
                audio_sinks.append(audio_sink)

        transcription_sources: list[pad.StatelessSourcePad] = []
        for i in range(num_participants.get_value() or 1):
            transcription_source = cast(
                pad.StatelessSourcePad, self.get_pad(f"transcription_{i}")
            )
            if transcription_source is None:
                transcription_source = pad.StatelessSourcePad(
                    id=f"transcription_{i}",
                    group="transcription",
                    owner_node=self,
                    default_type_constraints=[pad.types.String()],
                )
                transcription_sources.append(transcription_source)

        for p in self.pads:
            if p.get_group() == "audio" and p not in audio_sinks:
                self.pads.remove(p)

            if p.get_group() == "transcription" and p not in transcription_sources:
                self.pads.remove(p)

        speech_started_source = cast(
            pad.StatelessSourcePad, self.get_pad("speaking_started")
        )
        if speech_started_source is None:
            speech_started_source = pad.StatelessSourcePad(
                id="speaking_started",
                group="speaking_started",
                owner_node=self,
                default_type_constraints=[pad.types.Trigger()],
            )

        speech_ended_source = cast(pad.StatelessSourcePad, self.get_pad("speech_ended"))
        if speech_ended_source is None:
            speech_ended_source = pad.StatelessSourcePad(
                id="speech_ended",
                group="speech_ended",
                owner_node=self,
                default_type_constraints=[pad.types.Trigger()],
            )

        self.pads = cast(
            list[pad.Pad],
            (
                [service, api_key, num_participants]
                + audio_sinks
                + transcription_sources
                + [
                    speech_started_source,
                    speech_ended_source,
                ]
            ),
        )

    async def run(self):
        audio_sinks: list[pad.StatelessSinkPad] = []
        transcription_sources: list[pad.StatelessSourcePad] = []

        for p in self.pads:
            if p.get_group() == "audio":
                audio_sinks.append(cast(pad.StatelessSinkPad, p))

            if p.get_group() == "transcription":
                transcription_sources.append(cast(pad.StatelessSourcePad, p))

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

        async def create_stt_instance() -> stt.STT:
            if service.get_value() == "assembly_ai":
                api_key_pad = cast(
                    pad.PropertySinkPad, self.get_pad_required("api_key")
                )
                api_key_name = api_key_pad.get_value()
                api_key = await self.secret_provider.resolve_secret(api_key_name)
                return stt.Assembly(api_key=api_key)
            elif service.get_value() == "local_kyutai":
                return stt.Kyutai(port=8080)
            elif service.get_value() == "deepgram":
                api_key_pad = cast(
                    pad.PropertySinkPad, self.get_pad_required("api_key")
                )
                api_key_name = api_key_pad.get_value()
                api_key = await self.secret_provider.resolve_secret(api_key_name)
                return stt.Deepgram(api_key=api_key)
            else:
                logging.error("Unsupported STT service: %s", service.get_value())
                raise ValueError(f"Unsupported STT service: {service.get_value()}")

        talking_state = TalkingState()
        state_machine = _StateMachine(talking_state, SilentState())

        async def audio_sink_task(
            sink: pad.StatelessSinkPad, stt_impl: stt.STT
        ) -> None:
            async for audio in sink:
                if audio is None:
                    continue
                stt_impl.push_audio(audio.value)
                audio.ctx.complete()

        async def participant_task(
            idx: int,
            audio_sink: pad.StatelessSinkPad,
            transcription_source: pad.StatelessSourcePad,
        ) -> None:
            stt_impl = await create_stt_instance()
            stt_run_t = asyncio.create_task(stt_impl.run())
            audio_sink_t = asyncio.create_task(audio_sink_task(audio_sink, stt_impl))
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

            stt_impl.close()
            await asyncio.gather(stt_run_t, audio_sink_t)

        audio_sink_t = asyncio.create_task(audio_sink_task())
        kyutai_event_t = asyncio.create_task(stt_event_task())

        try:
            await asyncio.gather(stt_run_t, audio_sink_t, kyutai_event_t)
        except asyncio.CancelledError:
            pass
        finally:
            stt_impl.close()
            audio_sink_t.cancel()


class _State(Enum):
    SILENT = 0
    TALKING = 1
    AI_TALKING = 2
    IDLE = 3


class _StateMachine:
    def __init__(self, talking_state: "TalkingState"):
        pass

    pass


class TalkingState:
    def __init__(self):
        self._talking_values: dict[int, bool] = {}

    def set_talking(self, idx: int, talking: bool) -> None:
        self._talking_values[idx] = talking

    def is_anyone_talking(self) -> bool:
        return any(self._talking_values.values())


class _StateMachineBoolean:
    def __init__(self, initial: bool) -> None:
        pass

    pass
