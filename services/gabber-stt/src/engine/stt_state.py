import logging
import wave
from dataclasses import dataclass
from typing import Generic, TypeVar, TYPE_CHECKING


import numpy as np

if TYPE_CHECKING:
    from .engine import Engine

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseSTTState(Generic[T]):
    def __init__(self, *, engine: "Engine", state: T):
        self.name = self.__class__.__name__.split("_")[-1]
        self.engine = engine
        self.state = state

    async def tick(self): ...

    def vad_to_stt_curs(self, vad_curs: int) -> int:
        return self.engine.audio_window.convert_cursor(
            from_rate=self.engine.vad.sample_rate,
            to_rate=self.engine.stt.sample_rate,
            cursor=vad_curs,
        )

    def vad_to_eot_curs(self, vad_curs: int) -> int:
        return self.engine.audio_window.convert_cursor(
            from_rate=self.engine.vad.sample_rate,
            to_rate=self.engine.eot.sample_rate,
            cursor=vad_curs,
        )

    def vad_to_input_curs(self, vad_curs: int) -> int:
        return self.engine.audio_window.convert_cursor(
            from_rate=self.engine.vad.sample_rate,
            to_rate=self.engine._input_sample_rate,
            cursor=vad_curs,
        )

    async def vad_results(self, start_curs: int, end_curs: int) -> "list[VADResult]":
        results: list[VADResult] = []
        for i in range(
            start_curs,
            end_curs,
            self.engine.vad.inference_impl.new_audio_size,
        ):
            segment_end = min(
                i + self.engine.vad.inference_impl.new_audio_size, end_curs
            )
            segment_start = segment_end - self.engine.vad.inference_impl.full_audio_size
            if segment_start < 0:
                continue
            segment = self.engine.audio_window.get_segment(
                sample_rate=self.engine.vad.sample_rate,
                start_curs=segment_start,
                ends_curs=segment_end,
            )
            vad_value = await self.engine.vad.simple_inference(segment)
            results.append(
                VADResult(
                    start=i,
                    end=segment_end,
                    value=vad_value,
                )
            )
        return results

    @property
    def latest_vad_cursor(self):
        return self.engine.audio_window._end_cursors.get(self.engine.vad.sample_rate, 0)

    @property
    def latest_stt_cursor(self):
        return self.engine.audio_window._end_cursors.get(self.engine.stt.sample_rate, 0)


@dataclass
class NotTalkingState:
    vad_cursor: int
    trans_id: int = 0


class STTState_NotTalking(BaseSTTState[NotTalkingState]):
    async def tick(self):
        results: list[VADResult] = await self.vad_results(
            self.state.vad_cursor, self.latest_vad_cursor
        )

        start_talking = -1
        latest_talking = -1
        for vr in results:
            if (
                start_talking < 0
                and vr.value > self.engine.settings.initial_vad_threshold
            ):
                start_talking = vr.start
                latest_talking = vr.end

            if vr.value > self.engine.settings.vad_sustained_threshold:
                latest_talking = vr.end

            self.state.vad_cursor = vr.end

        if start_talking >= 0:
            logger.info(
                f"Detected start of speech at {start_talking}, {latest_talking}"
            )
            self.engine.transition_to(
                STTState_TalkingWarmUp(
                    engine=self.engine,
                    state=TalkingWarmUpState(
                        vad_cursor=self.state.vad_cursor,
                        start_talking=start_talking,
                        latest_voice=latest_talking,
                        trans_id=self.state.trans_id + 1,
                    ),
                )
            )


@dataclass
class TalkingWarmUpState:
    vad_cursor: int
    start_talking: int
    latest_voice: int
    trans_id: int


class STTState_TalkingWarmUp(BaseSTTState[TalkingWarmUpState]):
    async def tick(self):
        vads = await self.vad_results(self.state.vad_cursor, self.latest_vad_cursor)

        for vr in vads:
            if vr.value > self.engine.settings.vad_sustained_threshold:
                self.state.latest_voice = vr.end
            self.state.vad_cursor = vr.end

        voice_time = (
            self.state.latest_voice - self.state.start_talking
        ) / self.engine.vad.sample_rate

        stt_seg = self.engine.audio_window.get_segment(
            sample_rate=self.engine.stt.sample_rate,
            start_curs=self.vad_to_stt_curs(vad_curs=self.state.start_talking),
            ends_curs=self.vad_to_stt_curs(vad_curs=self.state.latest_voice),
        )
        stt_result = await self.engine.stt.simple_inference(stt_seg)
        if stt_result.transcription.strip() != "":
            self.engine.transition_to(
                STTState_Talking(
                    engine=self.engine,
                    state=STTTalkingState(
                        stt_cursor=self.vad_to_stt_curs(
                            vad_curs=self.state.start_talking,
                        ),
                        trans_id=self.state.trans_id,
                        start_talking=self.state.start_talking,
                        latest_voice=self.state.latest_voice,
                        vad_cursor=self.state.vad_cursor,
                    ),
                )
            )

        if voice_time >= self.engine.settings.speaking_started_warmup_time_s:
            self.engine.emit_event(
                STTEvent_SpeakingStarted(
                    trans_id=self.state.trans_id,
                    start_sample=self.vad_to_input_curs(
                        vad_curs=self.state.start_talking,
                    ),
                )
            )
            self.engine.transition_to(
                STTState_Talking(
                    engine=self.engine,
                    state=STTTalkingState(
                        stt_cursor=self.vad_to_stt_curs(
                            vad_curs=self.state.start_talking,
                        ),
                        trans_id=self.state.trans_id,
                        start_talking=self.state.start_talking,
                        latest_voice=self.state.latest_voice,
                        vad_cursor=self.state.vad_cursor,
                    ),
                )
            )
            return

        time_since_last_voice = (
            self.state.vad_cursor - self.state.latest_voice
        ) / self.engine.vad.sample_rate
        if (
            time_since_last_voice
            >= self.engine.settings.speaking_started_warmup_time_s * 2
        ):
            self.engine.transition_to(
                STTState_NotTalking(
                    engine=self.engine,
                    state=NotTalkingState(
                        vad_cursor=self.state.vad_cursor, trans_id=self.state.trans_id
                    ),
                )
            )


@dataclass
class STTTalkingState:
    trans_id: int
    start_talking: int
    stt_cursor: int
    vad_cursor: int
    latest_voice: int
    current_transcription: str = ""


class STTState_Talking(BaseSTTState[STTTalkingState]):
    async def tick(self):
        vads = await self.vad_results(self.state.vad_cursor, self.latest_vad_cursor)

        for vr in vads:
            if vr.value > self.engine.settings.vad_sustained_threshold:
                self.state.latest_voice = vr.end
            self.state.vad_cursor = vr.end

        time_since_last_voice = (
            self.state.vad_cursor - self.state.latest_voice
        ) / self.engine.vad.sample_rate

        if (
            self.latest_stt_cursor - self.state.stt_cursor
            > self.engine.stt.inference_impl.new_audio_size
        ):
            segment = self.engine.audio_window.get_segment(
                sample_rate=self.engine.stt.sample_rate,
                start_curs=self.vad_to_stt_curs(vad_curs=self.state.start_talking),
                ends_curs=self.latest_stt_cursor,
            )
            if segment.shape[0] < self.engine.stt.inference_impl.full_audio_size:
                logger.warning(
                    "STT segment smaller than full audio size, padding with zeros"
                )
            self.state.stt_cursor = self.latest_stt_cursor

            stt_result = await self.engine.stt.simple_inference(segment)
            self.state.current_transcription = stt_result.transcription
            self.engine.emit_event(
                STTEvent_InterimTranscription(
                    trans_id=self.state.trans_id,
                    start_sample=self.vad_to_input_curs(
                        vad_curs=self.state.start_talking,
                    ),
                    end_sample=self.vad_to_input_curs(
                        vad_curs=self.state.latest_voice,
                    ),
                    transcription=stt_result.transcription,
                )
            )

        if time_since_last_voice >= self.engine.settings.vad_cooldown_time_s:
            start_curs = self.vad_to_eot_curs(vad_curs=self.state.start_talking)
            end_curs = self.vad_to_eot_curs(vad_curs=self.state.vad_cursor)
            segment = self.engine.audio_window.get_segment(
                sample_rate=self.engine.eot.sample_rate,
                start_curs=start_curs,
                ends_curs=end_curs,
            )

            if segment.shape[0] < self.engine.eot.inference_impl.full_audio_size:
                left_padding = max(
                    0, self.engine.eot.inference_impl.full_audio_size - segment.shape[0]
                )
                if left_padding > 0:
                    segment = np.pad(
                        segment,
                        (left_padding, 0),
                    )
            elif segment.shape[0] > self.engine.eot.inference_impl.full_audio_size:
                segment = segment[-self.engine.eot.inference_impl.full_audio_size :]

            eot_result = await self.engine.eot.simple_inference(segment)
            if eot_result > 0.7:
                self.engine.transition_to(
                    STTState_Finalizing(
                        engine=self.engine,
                        state=FinalizingState(
                            current_transcription=self.state.current_transcription,
                            trans_id=self.state.trans_id,
                            start_talking=self.state.start_talking,
                            end_talking=self.state.latest_voice
                            + int(
                                self.engine.settings.vad_cooldown_time_s
                                * self.engine.vad.sample_rate
                                * 0.5
                            ),
                        ),
                    )
                )
                return

        if time_since_last_voice >= self.engine.settings.eot_timeout_s:
            self.engine.transition_to(
                STTState_Finalizing(
                    engine=self.engine,
                    state=FinalizingState(
                        current_transcription=self.state.current_transcription,
                        trans_id=self.state.trans_id,
                        start_talking=self.state.start_talking,
                        end_talking=self.state.latest_voice
                        + int(
                            self.engine.settings.vad_cooldown_time_s
                            * self.engine.vad.sample_rate
                            * 0.5
                        ),
                    ),
                )
            )


@dataclass
class FinalizingState:
    trans_id: int
    current_transcription: str
    start_talking: int
    end_talking: int


class STTState_Finalizing(BaseSTTState[FinalizingState]):
    async def tick(self):
        stt_seg = self.engine.audio_window.get_segment(
            sample_rate=self.engine.stt.sample_rate,
            start_curs=self.vad_to_stt_curs(self.state.start_talking),
            ends_curs=self.vad_to_stt_curs(self.state.end_talking),
        )
        final_stt = await self.engine.stt.simple_inference(stt_seg)
        # with wave.open(f"utterance_{self.state.trans_id}.wav", "wb") as wf:
        #     wf.setnchannels(1)
        #     wf.setsampwidth(2)
        #     wf.setframerate(self.engine._input_sample_rate)
        #     start_curs = self.vad_to_input_curs(vad_curs=self.state.start_talking)
        #     end_curs = self.vad_to_input_curs(vad_curs=self.state.end_talking)
        #     segment = self.engine.audio_window.get_segment(
        #         sample_rate=self.engine._input_sample_rate,
        #         start_curs=start_curs,
        #         ends_curs=end_curs,
        #     )
        #     wf.writeframes(segment.tobytes())
        self.engine.emit_event(
            STTEvent_FinalTranscription(
                trans_id=self.state.trans_id,
                transcription=final_stt.transcription,
                start_sample=self.vad_to_input_curs(self.state.start_talking),
                end_sample=self.vad_to_input_curs(self.state.end_talking),
            )
        )

        self.engine.transition_to(
            STTState_NotTalking(
                engine=self.engine,
                state=NotTalkingState(
                    vad_cursor=self.state.end_talking, trans_id=self.state.trans_id
                ),
            )
        )


@dataclass
class STTEvent_InterimTranscription:
    trans_id: int
    start_sample: int
    end_sample: int
    transcription: str


@dataclass
class STTEvent_SpeakingStarted:
    trans_id: int
    start_sample: int


@dataclass
class STTEvent_FinalTranscription:
    trans_id: int
    transcription: str
    start_sample: int
    end_sample: int


@dataclass
class VADResult:
    start: int
    end: int
    value: float


@dataclass
class EOTResult:
    start: int
    end: int
    value: float


@dataclass
class STTResult:
    start: int
    end: int
    transcription: str
