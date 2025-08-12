# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from collections import deque
from enum import Enum
from typing import cast

import numpy as np
from core import node, pad, runtime_types
from core.node import NodeMetadata
from core.runtime_types import AudioClip, AudioFrame
from lib.audio import vad
from numpy.typing import NDArray

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SUPPORTED_SAMPLE_RATE = 16000

VAD_CHUNK_SIZE = 512
VAD_STATE_SHAPE = (2, 1, 128)
PCM_16_NORMALIZATION_FACTOR = 32768.0


class SpeechState(Enum):
    """Speech detection states"""

    SILENT = "silent"
    SPEAKING = "speaking"
    ENDING = "ending"


class SileroVAD(node.Node):
    @classmethod
    def get_description(cls) -> str:
        return "Voice Activity Detection - detects when someone is speaking"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(primary="ai", secondary="audio", tags=["vad", "detection"])

    async def resolve_pads(self):
        audio_sink = cast(pad.StatelessSinkPad, self.get_pad("audio"))
        if not audio_sink:
            audio_sink = pad.StatelessSinkPad(
                id="audio",
                group="audio",
                owner_node=self,
                type_constraints=[pad.types.Audio()],
            )
            self.pads.append(audio_sink)

        audio_clip_source = cast(pad.StatelessSourcePad, self.get_pad("audio_clip"))
        if not audio_clip_source:
            audio_clip_source = pad.StatelessSourcePad(
                id="audio_clip",
                group="audio_clip",
                owner_node=self,
                type_constraints=[pad.types.AudioClip()],
            )
            self.pads.append(audio_clip_source)

        speech_started_trigger = cast(
            pad.StatelessSourcePad, self.get_pad("speech_started_trigger")
        )
        if not speech_started_trigger:
            speech_started_trigger = pad.StatelessSourcePad(
                id="speech_started_trigger",
                group="speech_started_trigger",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(speech_started_trigger)

        speech_ended_trigger = cast(
            pad.StatelessSourcePad, self.get_pad("speech_ended_trigger")
        )
        if not speech_ended_trigger:
            speech_ended_trigger = pad.StatelessSourcePad(
                id="speech_ended_trigger",
                group="speech_ended_trigger",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(speech_ended_trigger)

        continued_speech_trigger = cast(
            pad.StatelessSourcePad, self.get_pad("continued_speech_trigger")
        )
        if not continued_speech_trigger:
            continued_speech_trigger = pad.StatelessSourcePad(
                id="continued_speech_trigger",
                group="continued_speech_trigger",
                owner_node=self,
                type_constraints=[pad.types.Trigger()],
            )
            self.pads.append(continued_speech_trigger)

        vad_threshold = cast(pad.PropertySinkPad, self.get_pad("vad_threshold"))
        if not vad_threshold:
            vad_threshold = pad.PropertySinkPad(
                id="vad_threshold",
                group="vad_threshold",
                owner_node=self,
                type_constraints=[pad.types.Float(minimum=0.0, maximum=1.0)],
                value=0.5,
            )
            self.pads.append(vad_threshold)

        silence_duration_ms = cast(
            pad.PropertySinkPad, self.get_pad("silence_duration_ms")
        )
        if not silence_duration_ms:
            silence_duration_ms = pad.PropertySinkPad(
                id="silence_duration_ms",
                group="silence_duration_ms",
                owner_node=self,
                type_constraints=[pad.types.Float(minimum=0.0, maximum=3000.0)],
                value=500.0,
            )
            self.pads.append(silence_duration_ms)

        speech_duration_ms = cast(
            pad.PropertySinkPad, self.get_pad("speech_duration_ms")
        )
        if not speech_duration_ms:
            speech_duration_ms = pad.PropertySinkPad(
                id="speech_duration_ms",
                group="speech_duration_ms",
                owner_node=self,
                type_constraints=[pad.types.Float(minimum=0.0, maximum=3000.0)],
                value=400.0,
            )
            self.pads.append(speech_duration_ms)

        pre_speech_duration_ms = cast(
            pad.PropertySinkPad, self.get_pad("pre_speech_duration_ms")
        )
        if not pre_speech_duration_ms:
            pre_speech_duration_ms = pad.PropertySinkPad(
                id="pre_speech_duration_ms",
                group="pre_speech_duration_ms",
                owner_node=self,
                type_constraints=[pad.types.Float(minimum=0.0, maximum=1000.0)],
                value=100.0,
            )
            self.pads.append(pre_speech_duration_ms)

    def _convert_audio_data_to_float(
        self, audio_data: NDArray[np.int16]
    ) -> NDArray[np.float32] | None:
        # Assuming 16-bit PCM audio
        audio_samples = np.frombuffer(audio_data, dtype=np.int16)
        # Normalize to [-1, 1] range
        return audio_samples.astype(np.float32) / PCM_16_NORMALIZATION_FACTOR

    async def run(self):
        vad_threshold = cast(
            pad.PropertySinkPad, self.get_pad_required("vad_threshold")
        )
        silence_duration_ms = cast(
            pad.PropertySinkPad, self.get_pad_required("silence_duration_ms")
        )
        speech_duration_ms = cast(
            pad.PropertySinkPad, self.get_pad_required("speech_duration_ms")
        )
        pre_speech_duration_ms = cast(
            pad.PropertySinkPad, self.get_pad_required("pre_speech_duration_ms")
        )
        audio_sink = cast(pad.StatelessSinkPad, self.get_pad_required("audio"))
        logger.info("VAD node starting...")
        self._vad_engine = vad.SileroVAD()

        self._speech_state = SpeechState.SILENT
        self._silence_duration_ms_counter = 0.0
        self._speech_duration_ms_counter = 0.0
        self._continued_speech_emitted = False
        self._audio_accumulator: NDArray[np.float32] = np.array([], dtype=np.float32)

        self._speech_audio_frames = deque[AudioFrame]()
        self._pre_speech_buffer = deque[AudioFrame]()
        self._pre_speech_duration_ms = 0.0

        self._frame_count = 0

        logger.info(
            f"VAD node initialized - threshold: {vad_threshold.get_value()}, silence_duration: {silence_duration_ms.get_value()}ms, speech_duration: {speech_duration_ms.get_value()}ms, pre_speech_duration: {pre_speech_duration_ms.get_value()}ms"
        )

        async def audio_processing_task():
            try:
                async for audio_event in audio_sink:
                    await self._process_audio_frame(audio_event.value)
                    audio_event.ctx.complete()
            except Exception as e:
                logger.error(f"Error in VAD audio processing task: {e}", exc_info=True)

        await audio_processing_task()

    async def _process_audio_frame(self, frame: AudioFrame):
        """Process incoming audio frame with VAD"""
        self._frame_count += 1

        try:
            if frame.data_16000hz.sample_count == 0:
                return
            audio_data = frame.data_16000hz.fp32.reshape(1, -1).flatten()
            await self._process_vad_analysis(audio_data, frame)

        except Exception as e:
            logger.error(f"VAD processing error: {e}", exc_info=True)

    def _calculate_chunk_sizes(self, sample_rate: int) -> tuple[int, float]:
        """Calculate VAD chunk size and frame duration based on sample rate"""
        if sample_rate == SUPPORTED_SAMPLE_RATE:
            vad_chunk_size = VAD_CHUNK_SIZE
        else:
            # Calculate input chunk size that will resample to VAD_CHUNK_SIZE samples
            vad_chunk_size = VAD_CHUNK_SIZE * sample_rate // SUPPORTED_SAMPLE_RATE

        frame_duration_ms = (VAD_CHUNK_SIZE / SUPPORTED_SAMPLE_RATE) * 1000
        return vad_chunk_size, frame_duration_ms

    def _ensure_vad_chunk_size(
        self, vad_chunk: NDArray[np.float32]
    ) -> NDArray[np.float32]:
        """Ensure VAD chunk is exactly VAD_CHUNK_SIZE samples"""
        if len(vad_chunk) < VAD_CHUNK_SIZE:
            return np.pad(vad_chunk, (0, VAD_CHUNK_SIZE - len(vad_chunk)))
        elif len(vad_chunk) > VAD_CHUNK_SIZE:
            return vad_chunk[:VAD_CHUNK_SIZE]
        return vad_chunk

    def _update_speech_state(self, vad_prob: float, frame_duration_ms: float) -> None:
        """Update speech state based on VAD probability and emit triggers"""
        vad_threshold = cast(
            pad.PropertySinkPad, self.get_pad_required("vad_threshold")
        )
        speech_started_trigger = cast(
            pad.StatelessSourcePad, self.get_pad_required("speech_started_trigger")
        )
        speech_duration_ms = cast(
            pad.PropertySinkPad, self.get_pad_required("speech_duration_ms")
        )
        continued_speech_trigger = cast(
            pad.StatelessSourcePad, self.get_pad_required("continued_speech_trigger")
        )
        audio_clip_source = cast(
            pad.StatelessSourcePad, self.get_pad_required("audio_clip")
        )
        speech_ended_trigger = cast(
            pad.StatelessSourcePad, self.get_pad_required("speech_ended_trigger")
        )
        silence_duration_ms = cast(
            pad.PropertySinkPad, self.get_pad_required("silence_duration_ms")
        )
        threshold = vad_threshold.get_value()

        if vad_prob > threshold:
            if self._speech_state == SpeechState.SILENT:
                self._speech_state = SpeechState.SPEAKING
                self._speech_audio_frames = deque(self._pre_speech_buffer)
                self._pre_speech_buffer.clear()
                self._pre_speech_duration_ms = 0.0
                self._speech_duration_ms_counter = 0.0
                self._continued_speech_emitted = False
                speech_started_trigger.push_item(
                    runtime_types.Trigger(), pad.RequestContext(parent=None)
                )
            elif self._speech_state == SpeechState.ENDING:
                self._speech_state = SpeechState.SPEAKING

            self._silence_duration_ms_counter = 0.0

            # Track continued speech duration
            if self._speech_state == SpeechState.SPEAKING:
                self._speech_duration_ms_counter += frame_duration_ms

                # Check if continued speech duration exceeded and not yet emitted
                if (
                    not self._continued_speech_emitted
                    and self._speech_duration_ms_counter
                    >= speech_duration_ms.get_value()
                ):
                    continued_speech_trigger.push_item(
                        runtime_types.Trigger(), pad.RequestContext(parent=None)
                    )
                    self._continued_speech_emitted = True
                    logger.info(
                        f"Continued speech trigger emitted after {self._speech_duration_ms_counter:.1f}ms"
                    )
        else:
            # No speech detected
            if self._speech_state == SpeechState.SPEAKING:
                self._speech_state = SpeechState.ENDING
                self._silence_duration_ms_counter = 0.0
                # Reset speech duration tracking when speech ends
                self._speech_duration_ms_counter = 0.0
                self._continued_speech_emitted = False
            elif self._speech_state == SpeechState.ENDING:
                self._silence_duration_ms_counter += frame_duration_ms
                # Check if silence duration exceeded
                if self._silence_duration_ms_counter >= silence_duration_ms.get_value():
                    self._speech_state = SpeechState.SILENT
                    self._vad_engine.reset_states()

                    # Emit speech ended trigger and audio clip
                    if self._speech_audio_frames:
                        audio_clip = list(self._speech_audio_frames)
                        audio_clip_source.push_item(
                            AudioClip(audio=audio_clip), pad.RequestContext(parent=None)
                        )

                    speech_ended_trigger.push_item(
                        runtime_types.Trigger(), pad.RequestContext(parent=None)
                    )
                    logger.info(
                        f"Speech ENDED after {self._silence_duration_ms_counter:.1f}ms silence - trigger emitted"
                    )

                    # Clear collected frames
                    self._speech_audio_frames.clear()

    async def _process_vad_analysis(
        self, data: NDArray[np.float32], frame: AudioFrame
    ) -> None:
        """Process VAD analysis and collect speech frames"""
        vad_chunk_size, frame_duration_ms = self._calculate_chunk_sizes(16000)

        # Calculate incoming frame duration
        incoming_frame_duration_ms = (len(data) / 16000) * 1000.0

        # Manage pre-speech buffer if silent
        if self._speech_state == SpeechState.SILENT:
            self._pre_speech_buffer.append(frame)
            self._pre_speech_duration_ms += incoming_frame_duration_ms
            pre_speech_ms = cast(
                pad.PropertySinkPad, self.get_pad_required("pre_speech_duration_ms")
            ).get_value()
            while (
                self._pre_speech_duration_ms > pre_speech_ms
                and len(self._pre_speech_buffer) > 1
            ):
                popped = self._pre_speech_buffer.popleft()
                popped_duration = (
                    popped.data_16000hz.sample_count / popped.data_16000hz.sample_rate
                ) * 1000.0
                self._pre_speech_duration_ms -= popped_duration

        # Append new audio data to accumulator
        if len(self._audio_accumulator) == 0:
            self._audio_accumulator = data
        else:
            self._audio_accumulator = np.concatenate([self._audio_accumulator, data])

        # Collect audio frames during speech (including transition periods)
        if self._speech_state in [SpeechState.SPEAKING, SpeechState.ENDING]:
            self._speech_audio_frames.append(frame)

        vad_results = []
        while len(self._audio_accumulator) >= vad_chunk_size:
            chunk = self._audio_accumulator[:vad_chunk_size].astype(np.float32)
            self._audio_accumulator = self._audio_accumulator[vad_chunk_size:]

            vad_prob = self._vad_engine.inference(chunk)
            vad_results.append(vad_prob)

        if vad_results:
            vad_prob = vad_results[-1]
            self._update_speech_state(vad_prob, frame_duration_ms)
