import asyncio
from itertools import batched
import logging
import threading
import wave
from dataclasses import dataclass
from time import time
from typing import Any, cast

import numpy as np
import torch
from core import AudioInferenceInternalResult, AudioInferenceRequest
from nemo.collections.asr.parts.submodules.transducer_decoding.label_looping_base import (
    BatchedLabelLoopingState,
    LabelLoopingStateItem,
)
from nemo.collections.asr.parts.utils.rnnt_utils import (
    BatchedHyps,
    Hypothesis,
    batched_hyps_to_hypotheses,
)
from nemo.collections.asr.parts.utils.timestamp_utils import process_timestamp_outputs

from ..stt import STTInference, STTInferenceResult, STTInferenceResultWord
from .model import CanaryModelInstance, load_model


def make_divisible_by(num, factor: int) -> int:
    """Make num divisible by factor"""
    return int((num // factor) * factor)


# High level strategy comes from:
# https://github.com/NVIDIA-NeMo/NeMo/blob/main/examples/asr/asr_chunked_inference/rnnt/speech_to_text_streaming_infer_rnnt.py
class ParakeetSTTInference(STTInference):
    def __init__(
        self,
        *,
        window_secs: float = 10.0,
        chunk_secs: float = 0.320,
    ):
        self._window_sec = window_secs
        self._chunk_secs = chunk_secs
        self._model: CanaryModelInstance | None = None

    @property
    def sample_rate(self) -> int:
        return 16000

    @property
    def new_audio_size(self) -> int:
        assert self._model is not None, "Model not initialized"
        return make_divisible_by(
            self.sample_rate * self._chunk_secs,
            self._model.encoder_frame_2_audio_samples,
        )  # type: ignore

    @property
    def full_audio_size(self) -> int:
        assert self._model is not None, "Model not initialized"
        return make_divisible_by(
            self.sample_rate * self._window_sec,
            self.new_audio_size,
        )

    def _initialize_model(self):
        self._model = load_model()

    async def initialize(self) -> None:
        init_thread = threading.Thread(target=self._initialize_model)
        init_thread.start()
        await asyncio.get_event_loop().run_in_executor(None, init_thread.join, 120)
        if self._model is None:
            raise RuntimeError("Parakeet model initialization timed out")

    def inference(
        self, input: AudioInferenceRequest
    ) -> list[AudioInferenceInternalResult[STTInferenceResult]]:
        assert self._model is not None

        if input.audio_batch.shape[1] != self.full_audio_size:
            raise ValueError(f"Invalid audio size: {input.audio_batch.shape[1]}")

        batch = ParakeetInferenceBatch(
            chunk_size=self.new_audio_size,
            full_audio_size=self.full_audio_size,
            input=input,
            model=self._model,
        )

        encode_res = batch.encode()
        prev_states = [p.prev_decoder_state for p in input.prev_states if p is not None]
        prev_hyps = [p.prev_hyp for p in input.prev_states if p is not None]
        decode_results = batch.decode(
            encode_result=encode_res,
            prev_states=prev_states,
            prev_hyps=prev_hyps,
        )
        results: list[STTInferenceResult] = []
        for i in range(len(input.audio_batch)):
            results.append(
                STTInferenceResult(
                    transcription=decode_results[i].transcription,
                    words=[
                        STTInferenceResultWord(
                            word=w.text,
                            start_cursor=w.start_offset,
                            end_cursor=w.end_offset,
                        )
                        for w in decode_results[i].words
                    ],
                    start_cursor=0,
                    end_cursor=0,
                )
            )

        return [
            AudioInferenceInternalResult[STTInferenceResult](
                result=results[i],
                state=ParakeetSTTInferenceState(
                    prev_hyp=decode_results[i].hyp,
                    prev_decoder_state=decode_results[i].decode_state,
                ),
            )
            for i in range(len(input.audio_batch))
        ]


class ParakeetInferenceBatch:
    def __init__(
        self,
        *,
        chunk_size: int,
        full_audio_size: int,
        input: AudioInferenceRequest,
        model: CanaryModelInstance,
    ):
        self._chunk_frames = int(chunk_size // model.encoder_frame_2_audio_samples)
        self._left_context_features = (
            int(full_audio_size // model.encoder_frame_2_audio_samples)
            - self._chunk_frames
        )
        self.model = model
        self.input = input

    def encode(self):
        prev_states: list[ParakeetSTTInferenceState | None] = []
        for ps in self.input.prev_states:
            prev_states.append(ps)

        torch_audio_batch = (
            torch.from_numpy(self.input.audio_batch).to(torch.float32) / 32768.0
        ).to(self.model.encoder.device)
        input_signal_lengths = torch.zeros(
            [torch_audio_batch.shape[0]], dtype=torch.int64
        ).to(self.model.encoder.device)

        for i in range(torch_audio_batch.shape[0]):
            input_signal_lengths[i] = self.input.num_samples[i]

        encoder_output, encoder_output_len = self.model.encoder(
            input_signal=torch_audio_batch,
            input_signal_length=input_signal_lengths,
        )
        encoder_output = encoder_output.transpose(1, 2)

        encoder_contexts = torch.zeros(
            [
                encoder_output.shape[0],
                self._left_context_features + self._chunk_frames,
                encoder_output.shape[2],
            ],
            dtype=encoder_output.dtype,
            device=encoder_output.device,
        )
        encoder_context_lens = torch.zeros(
            [self.input.audio_batch.shape[0]], dtype=torch.int64
        ).to(encoder_output.device)

        continuations: list[bool] = []

        for i, p in enumerate(prev_states):
            input_features = (
                input_signal_lengths[i] // self.model.encoder_frame_2_audio_samples
            ).item()

            if input_features <= self._left_context_features:
                encoder_context_lens[i] = input_features
                encoder_contexts[i, :input_features] = encoder_output[
                    i, :input_features
                ]
                continuations.append(False)
            else:
                new_features = input_features - self._left_context_features
                encoder_context_lens[i] = new_features
                encoder_contexts[i, :new_features, :] = encoder_output[
                    i, input_features : input_features + new_features, :
                ]
                continuations.append(True)

        return InternalEncodeResult(
            encoder_contexts=encoder_contexts,
            encoder_context_lens=encoder_context_lens,
            continuations=continuations,
        )

    def decode(
        self,
        *,
        encode_result: "InternalEncodeResult",
        prev_states: list[LabelLoopingStateItem | None],
        prev_hyps: list[Hypothesis | None],
    ):
        states_to_merge: list[LabelLoopingStateItem | None] = []
        for i, cnt in enumerate(encode_result.continuations):
            if cnt:
                print("NEIL prev states", prev_states[i])
                states_to_merge.append(prev_states[i])
            else:
                states_to_merge.append(None)

        batched_state = None
        if any(ds is not None for ds in states_to_merge):
            batched_state = self.model.decoder.merge_to_batched_state(states_to_merge)

        chunk_batched_hyps, batched_alignments, state = self.model.decoder(
            x=encode_result.encoder_contexts,
            out_len=encode_result.encoder_context_lens,
            prev_batched_state=batched_state,
        )
        split_hypotheses = batched_hyps_to_hypotheses(
            chunk_batched_hyps,
            batched_alignments,
            batch_size=chunk_batched_hyps.batch_size,
        )
        split_states = self.model.decoder.split_batched_state(state)
        result: list[DecodeResult] = []
        for i, h in enumerate(split_hypotheses):
            assert isinstance(h, Hypothesis)
            txt = self.model.encoder.tokenizer.ids_to_text(h.y_sequence.tolist())
            print("NEIL txt", txt)
            token_repetitions = [
                len(self.model.encoder.tokenizer.ids_to_text([id]))
                for id in h.y_sequence.tolist()
            ]
            h.text = (h.y_sequence, h.alignments, token_repetitions)  # type: ignore
            h = self.model.encoder.decoding.compute_rnnt_timestamps(h)  # type: ignore
            ts_res = process_timestamp_outputs(
                h,
                subsampling_factor=self.model.encoder.encoder.subsampling_factor,
                window_stride=self.model.encoder.cfg["preprocessor"]["window_stride"],
            )
            words = [
                DecodeWord(
                    text=w["word"],
                    start_offset=w["start_offset"],
                    end_offset=w["end_offset"],
                )
                for w in ts_res[0].timestamp["word"]
            ]
            segments = [
                DecodeSegment(
                    start_offset=s["start_offset"],
                    end_offset=s["end_offset"],
                    segment=s["segment"],
                )
                for s in ts_res[0].timestamp["segment"]
            ]
            characters = [
                DecodeCharacter(
                    text=c["char"],
                    start_offset=c["start_offset"],
                    end_offset=c["end_offset"],
                )
                for c in ts_res[0].timestamp["char"]
            ]
            result.append(
                DecodeResult(
                    transcription=h.text,
                    words=words,
                    characters=characters,
                    segments=segments,
                    decode_state=split_states[i],
                    hyp=h,
                )
            )

        return result


@dataclass
class InternalEncodeResult:
    encoder_contexts: torch.Tensor
    encoder_context_lens: torch.Tensor
    continuations: list[bool]


@dataclass
class DecodeWord:
    text: str
    start_offset: int
    end_offset: int


@dataclass
class DecodeCharacter:
    text: str
    start_offset: int
    end_offset: int


@dataclass
class DecodeSegment:
    start_offset: int
    end_offset: int
    segment: str


@dataclass
class DecodeResult:
    transcription: str
    words: list[DecodeWord]
    characters: list[DecodeCharacter]
    segments: list[DecodeSegment]
    decode_state: LabelLoopingStateItem
    hyp: Hypothesis


@dataclass
class ParakeetSTTInferenceState:
    prev_hyp: Hypothesis | None
    prev_decoder_state: LabelLoopingStateItem | None
