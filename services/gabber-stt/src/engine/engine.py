import asyncio
import logging
import time
import wave
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

import numpy as np
from core import AudioWindow
from lib import eot, stt, vad

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class EngineSettings:
    initial_vad_threshold: float = 0.5
    vad_sustained_threshold: float = 0.25
    speaking_started_warmup_time_s: float = 0.1
    vad_cooldown_time_s: float = 0.5
    eot_timeout_s: float = 1.5


class Engine:
    def __init__(
        self,
        *,
        input_sample_rate: int,
        eot: eot.EndOfTurnEngine,
        vad: vad.VADInferenceEngine,
        stt: stt.STTInferenceEngine,
        settings: EngineSettings = EngineSettings(),
    ):
        self._input_sample_rate = input_sample_rate
        self.eot = eot
        self.vad = vad
        self.stt = stt
        self.audio_window = AudioWindow(
            max_length_s=60.0,
            sample_rates=[
                self.vad.sample_rate,
                self.stt.sample_rate,
                self.eot.sample_rate,
            ],
            input_sample_rate=input_sample_rate,
        )
        self._tasks = []
        self.settings = settings
        self.current_state: BaseEngineState = EngineState_NotTalking(
            engine=self, state=NotTalkingState(vad_cursor=0)
        )
        self._on_event: Callable[[EngineEvent], None] = lambda _: None

    def set_event_handler(self, h: "Callable[[EngineEvent], None]"):
        self._on_event = h

    def push_audio(self, audio: bytes):
        original_np_data = np.frombuffer(audio, dtype=np.int16)
        self.audio_window.push_audio(audio=original_np_data)

    async def run(self):
        while True:
            await self.current_state.tick()
            await asyncio.sleep(0.01)

    def transition_to(self, new_state: "BaseEngineState[T]"):
        logger.info(f"Transitioning from {self.current_state.name} to {new_state.name}")
        self.current_state = new_state

    def emit_event(self, evt: "EngineEvent"):
        self._on_event(evt)


class BaseEngineState(Generic[T]):
    def __init__(self, *, engine: Engine, state: T):
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
            if segment_end - i < self.engine.vad.inference_impl.new_audio_size:
                break
            segment = self.engine.audio_window.get_segment(
                sample_rate=self.engine.vad.sample_rate,
                start_curs=i,
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


class EngineState_NotTalking(BaseEngineState[NotTalkingState]):
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
                EngineState_TalkingWarmUp(
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


class EngineState_TalkingWarmUp(BaseEngineState[TalkingWarmUpState]):
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
                EngineState_Talking(
                    engine=self.engine,
                    state=EngineTalkingState(
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
                EngineEvent_SpeakingStarted(
                    trans_id=self.state.trans_id,
                    start_sample=self.vad_to_input_curs(
                        vad_curs=self.state.start_talking,
                    ),
                )
            )
            self.engine.transition_to(
                EngineState_Talking(
                    engine=self.engine,
                    state=EngineTalkingState(
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
                EngineState_NotTalking(
                    engine=self.engine,
                    state=NotTalkingState(
                        vad_cursor=self.state.vad_cursor, trans_id=self.state.trans_id
                    ),
                )
            )


@dataclass
class EngineTalkingState:
    trans_id: int
    start_talking: int
    stt_cursor: int
    vad_cursor: int
    latest_voice: int
    current_transcription: str = ""


class EngineState_Talking(BaseEngineState[EngineTalkingState]):
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
            self.state.stt_cursor = self.latest_stt_cursor

            stt_result = await self.engine.stt.simple_inference(segment)
            self.state.current_transcription = stt_result.transcription
            self.engine.emit_event(
                EngineEvent_InterimTranscription(
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
                    EngineState_Finalizing(
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
                EngineState_Finalizing(
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


class EngineState_Finalizing(BaseEngineState[FinalizingState]):
    async def tick(self):
        stt_seg = self.engine.audio_window.get_segment(
            sample_rate=self.engine.stt.sample_rate,
            start_curs=self.vad_to_stt_curs(self.state.start_talking),
            ends_curs=self.vad_to_stt_curs(self.state.end_talking),
        )
        final_stt = await self.engine.stt.simple_inference(stt_seg)
        with wave.open(f"utterance_{self.state.trans_id}.wav", "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.engine._input_sample_rate)
            start_curs = self.vad_to_input_curs(vad_curs=self.state.start_talking)
            end_curs = self.vad_to_input_curs(vad_curs=self.state.end_talking)
            segment = self.engine.audio_window.get_segment(
                sample_rate=self.engine._input_sample_rate,
                start_curs=start_curs,
                ends_curs=end_curs,
            )
            wf.writeframes(segment.tobytes())
        self.engine.emit_event(
            EngineEvent_FinalTranscription(
                trans_id=self.state.trans_id,
                transcription=final_stt.transcription,
                start_sample=self.vad_to_input_curs(self.state.start_talking),
                end_sample=self.vad_to_input_curs(self.state.end_talking),
            )
        )

        self.engine.transition_to(
            EngineState_NotTalking(
                engine=self.engine,
                state=NotTalkingState(
                    vad_cursor=self.state.end_talking, trans_id=self.state.trans_id
                ),
            )
        )


@dataclass
class EngineEvent_Error:
    message: str


@dataclass
class EngineEvent_InterimTranscription:
    trans_id: int
    start_sample: int
    end_sample: int
    transcription: str


@dataclass
class EngineEvent_SpeakingStarted:
    trans_id: int
    start_sample: int


@dataclass
class EngineEvent_FinalTranscription:
    trans_id: int
    transcription: str
    start_sample: int
    end_sample: int


EngineEvent = (
    EngineEvent_Error
    | EngineEvent_FinalTranscription
    | EngineEvent_InterimTranscription
    | EngineEvent_SpeakingStarted
)


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
