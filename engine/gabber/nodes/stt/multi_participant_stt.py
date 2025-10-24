# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast, Callable

from gabber.core import node, pad
from gabber.core.types import runtime
from gabber.core.node import NodeMetadata
from gabber.lib import stt
from enum import Enum
from gabber.core.types import pad_constraints


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
                    pad_constraints.Enum(
                        options=["assembly_ai", "local_kyutai", "deepgram"]
                    )
                ],
                value="assembly_ai",
            )

        api_key = cast(pad.PropertySinkPad, self.get_pad("api_key"))
        if api_key is None:
            api_key = pad.PropertySinkPad(
                id="api_key",
                group="api_key",
                owner_node=self,
                default_type_constraints=[pad_constraints.Secret(options=self.secrets)],
                value=None,
            )

        num_participants = cast(pad.PropertySinkPad, self.get_pad("num_participants"))
        if num_participants is None:
            num_participants = pad.PropertySinkPad(
                id="num_participants",
                group="num_participants",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer()],
                value=2,
            )

        cooldown_time_ms = cast(pad.PropertySinkPad, self.get_pad("cooldown_time_ms"))
        if cooldown_time_ms is None:
            cooldown_time_ms = pad.PropertySinkPad(
                id="cooldown_time_ms",
                group="cooldown_time_ms",
                owner_node=self,
                default_type_constraints=[pad_constraints.Integer()],
                value=4000,
            )

        force_ai_talk = cast(pad.StatelessSinkPad, self.get_pad("force_ai_talk"))
        if force_ai_talk is None:
            force_ai_talk = pad.StatelessSinkPad(
                id="force_ai_talk",
                group="force_ai_talk",
                owner_node=self,
                default_type_constraints=[pad_constraints.Trigger()],
            )

        current_state = cast(pad.PropertySourcePad, self.get_pad("current_state"))
        if current_state is None:
            current_state = pad.PropertySourcePad(
                id="current_state",
                group="current_state",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.Enum(options=[e.name for e in State])
                ],
                value=State.WAITING_FOR_HUMAN.name,
            )

        previous_state = cast(pad.PropertySourcePad, self.get_pad("previous_state"))
        if previous_state is None:
            previous_state = pad.PropertySourcePad(
                id="previous_state",
                group="previous_state",
                owner_node=self,
                default_type_constraints=[
                    pad_constraints.Enum(options=[e.name for e in State])
                ],
                value=State.WAITING_FOR_HUMAN.name,
            )

        audio_sinks: list[pad.StatelessSinkPad] = []
        for i in range(num_participants.get_value() or 1):
            audio_sink = cast(pad.StatelessSinkPad, self.get_pad(f"audio_{i}"))
            if audio_sink is None:
                audio_sink = pad.StatelessSinkPad(
                    id=f"audio_{i}",
                    group="audio",
                    owner_node=self,
                    default_type_constraints=[pad_constraints.Audio()],
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
                    default_type_constraints=[pad_constraints.String()],
                )
            transcription_sources.append(transcription_source)

        for p in self.pads:
            if p.get_group() == "audio" and p not in audio_sinks:
                self.pads.remove(p)

            if p.get_group() == "transcription" and p not in transcription_sources:
                self.pads.remove(p)

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

        self.pads = cast(
            list[pad.Pad],
            (
                [
                    current_state,
                    previous_state,
                    service,
                    api_key,
                    num_participants,
                    cooldown_time_ms,
                    force_ai_talk,
                ]
                + audio_sinks
                + transcription_sources
                + [
                    speech_started_source,
                    speech_ended_source,
                ]
            ),
        )

    async def create_stt_instance(self) -> stt.STT:
        service = cast(pad.PropertySinkPad, self.get_pad_required("service"))
        if service.get_value() == "assembly_ai":
            api_key_pad = self.get_property_sink_pad_required(runtime.Secret, "api_key")
            api_key = await self.secret_provider.resolve_secret(
                api_key_pad.get_value().secret_id
            )
            return stt.Assembly(api_key=api_key)
        elif service.get_value() == "local_kyutai":
            return stt.Kyutai(port=8080)
        elif service.get_value() == "deepgram":
            api_key_pad = self.get_property_sink_pad_required(runtime.Secret, "api_key")
            api_key = await self.secret_provider.resolve_secret(
                api_key_pad.get_value().secret_id
            )
            return stt.Deepgram(api_key=api_key)
        else:
            logging.error("Unsupported STT service: %s", service.get_value())
            raise ValueError(f"Unsupported STT service: {service.get_value()}")

    async def run(self):
        audio_sinks: list[pad.StatelessSinkPad] = []
        transcription_sources: list[pad.StatelessSourcePad] = []

        for p in self.pads:
            if p.get_group() == "audio":
                audio_sinks.append(cast(pad.StatelessSinkPad, p))

            if p.get_group() == "transcription":
                transcription_sources.append(cast(pad.StatelessSourcePad, p))

        speech_started_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("speech_started")
        )
        speech_ended_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("speech_ended")
        )
        current_state = cast(
            pad.PropertySourcePad, self.get_pad_required("current_state")
        )
        previous_state = cast(
            pad.PropertySourcePad, self.get_pad_required("previous_state")
        )
        force_ai_talk = cast(
            pad.StatelessSinkPad, self.get_pad_required("force_ai_talk")
        )

        def sm_callback(old_state: State, new_state: State) -> None:
            ctx = pad.RequestContext(parent=None, publisher_metadata=None)
            previous_state.push_item(old_state.name, ctx)
            current_state.push_item(new_state.name, ctx)

        talking_state = TalkingState()
        state_machine = StateMachine(
            talking_state,
            cb=sm_callback,
            cooldown_pad=cast(
                pad.PropertySinkPad, self.get_pad_required("cooldown_time_ms")
            ),
        )

        async def audio_sink_task(
            sink: pad.StatelessSinkPad,
            stt_impl: stt.STT,
            md_promise: asyncio.Future[dict[str, str] | None],
        ) -> None:
            async for audio in sink:
                if not md_promise.done():
                    md_promise.set_result(audio.ctx.publisher_metadata)
                if audio is None:
                    continue
                stt_impl.push_audio(audio.value)
                audio.ctx.complete()

        async def participant_task(
            idx: int,
            audio_sink: pad.StatelessSinkPad,
            transcription_source: pad.StatelessSourcePad,
        ) -> None:
            stt_impl = await self.create_stt_instance()
            stt_run_t = asyncio.create_task(stt_impl.run())
            md_promise: asyncio.Future[dict[str, str] | None] = asyncio.Future()
            audio_sink_t = asyncio.create_task(
                audio_sink_task(audio_sink, stt_impl, md_promise)
            )
            ctx: pad.RequestContext | None = None
            md: dict[str, str] | None = await md_promise
            async for event in stt_impl:
                if isinstance(event, stt.STTEvent_SpeechStarted):
                    talking_state.set_talking(idx, True)
                    ctx = pad.RequestContext(parent=None, publisher_metadata=md)
                    speech_started_source.push_item(runtime.Trigger(), ctx)
                elif isinstance(event, stt.STTEvent_Transcription):
                    # TODO
                    pass
                elif isinstance(event, stt.STTEvent_EndOfTurn):
                    talking_state.set_talking(idx, False)
                    txt = event.clip.transcription
                    if txt is None:
                        txt = ""

                    if ctx is None:
                        logging.error(
                            "Received STTEvent_EndOfTurn without a context. This should not happen."
                        )
                        continue

                    transcription_source.push_item(txt, ctx)
                    speech_ended_source.push_item(runtime.Trigger(), ctx)
                    ctx.complete()

            stt_impl.close()
            await asyncio.gather(stt_run_t, audio_sink_t)

        async def force_ai_talk_task() -> None:
            async for _ in force_ai_talk:
                state_machine.force_ai_talk()

        participant_tasks = []
        for i in range(len(audio_sinks)):
            participant_tasks.append(
                asyncio.create_task(
                    participant_task(i, audio_sinks[i], transcription_sources[i])
                )
            )

        try:
            await asyncio.gather(*participant_tasks, force_ai_talk_task())
        except asyncio.CancelledError:
            pass


class State(Enum):
    WAITING_FOR_HUMAN = 0
    TALKING = 1
    COOLDOWN = 2
    AI_CAN_TALK = 3


class StateMachine:
    def __init__(
        self,
        talking_state: "TalkingState",
        cooldown_pad: pad.PropertySinkPad,
        cb: Callable[[State, State], None] = lambda old_state, new_state: None,
    ):
        self._cooldown_pad = cooldown_pad
        self._talking_state = talking_state
        self._talking_state.cb = self._talking_changed
        self._state = State.WAITING_FOR_HUMAN
        self._cb = cb
        self._cooldown_task: asyncio.Task[None] | None = None

    def _talking_changed(self, talking: bool) -> None:
        if talking:
            self._set_state(State.TALKING)
            if self._cooldown_task is not None:
                self._cooldown_task.cancel()
            self._cooldown_task = asyncio.create_task(self._cooldown_timer())
        elif self._state == State.TALKING:
            self._set_state(State.COOLDOWN)

    def _set_state(self, new_state: State) -> None:
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._cb(old_state, new_state)

    async def _cooldown_timer(self) -> None:
        cooldown_time_ms = self._cooldown_pad.get_value() or 4000
        await asyncio.sleep(cooldown_time_ms / 1000.0)
        if not self._talking_state.is_anyone_talking():
            self._set_state(State.AI_CAN_TALK)
        self._cooldown_task = None

    def force_ai_talk(self) -> None:
        if self._cooldown_task is not None:
            self._cooldown_task.cancel()
            self._cooldown_task = None
        self._set_state(State.AI_CAN_TALK)


class TalkingState:
    def __init__(self):
        self._talking_values: dict[int, bool] = {}
        self._talking = False
        self.cb: Callable[[bool], None] = lambda talking: None

    def set_talking(self, idx: int, talking: bool) -> None:
        self._talking_values[idx] = talking
        prev = self._talking
        self._talking = self.is_anyone_talking()
        if prev != self._talking:
            self.cb(self._talking)

    def is_anyone_talking(self) -> bool:
        return any(self._talking_values.values())
