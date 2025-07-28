# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import cast

from core import node, pad, runtime_types
from core.node import NodeMetadata
from lib import stt


class KyutaiSTT(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Speech-to-Text using Kyutai's STT model"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            primary="ai", secondary="audio", tags=["stt", "speech", "kyutai"]
        )

    async def resolve_pads(self):
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

        self._kyutai = stt.Kyutai(port=8080)
        kyutai_run_t = asyncio.create_task(self._kyutai.run())

        async def audio_sink_task() -> None:
            async for audio in audio_sink:
                if audio is None:
                    continue
                self._kyutai.push_audio(audio.value)
                audio.ctx.complete()

        async def kyutai_event_task() -> None:
            ctx: pad.RequestContext | None = None
            async for event in self._kyutai:
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
        kyutai_event_t = asyncio.create_task(kyutai_event_task())

        try:
            await asyncio.gather(kyutai_run_t, audio_sink_t, kyutai_event_t)
        except asyncio.CancelledError:
            pass
        finally:
            self._kyutai.close()
            audio_sink_t.cancel()
