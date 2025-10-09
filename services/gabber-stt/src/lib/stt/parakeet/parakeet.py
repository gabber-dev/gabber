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
    ):
        self._window_sec = window_secs

        self._model: CanaryModelInstance | None = None

    @property
    def sample_rate(self) -> int:
        return 16000

    @property
    def new_audio_size(self) -> int:
        return 1600 * 2

    @property
    def window_samples(self):
        assert self._model is not None, "Model not initialized"
        window_samples = make_divisible_by(
            self.sample_rate * self._window_sec,
            self._model.encoder_frame_2_audio_samples,
        )
        return window_samples

    @property
    def window_encoder_frames(self):
        assert self._model is not None, "Model not initialized"
        return int(self.window_samples / self._model.encoder_frame_2_audio_samples)

    @property
    def full_audio_size(self) -> int:
        return self.window_samples

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
        batch.decode(encode_res)
        results: list[STTInferenceResult] = []
        for i in range(len(input.audio_batch)):
            results.append(
                STTInferenceResult(
                    transcription="",
                    words=[],
                    start_cursor=0,
                    end_cursor=0,
                )
            )

        return [
            AudioInferenceInternalResult[STTInferenceResult](
                result=results[i],
                state=ParakeetSTTInferenceState(
                    abs_context_cursor=encode_res.absolute_context_curss[i],
                    abs_window_start_cursor=encode_res.absolute_window_curss[i],
                    abs_finalize_curs=encode_res.absolute_finalize_curss[i],
                    full_window=encode_res.full_windows[i],
                    latest_hyp=encode_res.finalized_hyps[i],
                    latest_decoder_state=encode_res.finalized_decoder_states[i],
                ),
            )
            for i in range(len(input.audio_batch))
        ]

    def decode_batch(
        self,
        encoder_features: torch.Tensor,
        batch_idxs: list[int],
    ) -> "list[DecodeResult]":
        if len(batch_idxs) == 0:
            return []

        assert self._model is not None

        decoder_state: BatchedLabelLoopingState | None = None

        batch_features = torch.zeros(
            len(batch_idxs),
            *encoder_features.shape[1:],
            device=encoder_features.device,
            dtype=encoder_features.dtype,
        )
        for i, bidx in enumerate(batch_idxs):
            batch_features[i, :] = encoder_features[bidx, :]

        chunk_batched_hyps, batched_alignments, state = self._model.decoder(
            x=batch_features.to(self._model.encoder.device),
            out_len=torch.tensor(
                [self.window_encoder_frames] * batch_features.shape[0]
            ),
            prev_batched_state=decoder_state,
        )

        split_hypotheses = batched_hyps_to_hypotheses(
            chunk_batched_hyps,
            batched_alignments,
            batch_size=chunk_batched_hyps.batch_size,
        )
        split_states = self._model.decoder.split_batched_state(state)

        result: list[DecodeResult] = []
        for i, h in enumerate(split_hypotheses):
            assert isinstance(h, Hypothesis)
            token_repetitions = [
                len(self._model.encoder.tokenizer.ids_to_text([id]))
                for id in h.y_sequence.tolist()
            ]
            h.text = (h.y_sequence, h.alignments, token_repetitions)  # type: ignore
            h = self._model.encoder.decoding.compute_rnnt_timestamps(h)  # type: ignore
            ts_res = process_timestamp_outputs(
                h,
                subsampling_factor=self._model.encoder.encoder.subsampling_factor,
                window_stride=self._model.encoder.cfg["preprocessor"]["window_stride"],
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
                )
            )

        return result


class ParakeetInferenceBatch:
    def __init__(
        self,
        *,
        chunk_size: int,
        full_audio_size: int,
        input: AudioInferenceRequest,
        model: CanaryModelInstance,
    ):
        self.chunk_size = chunk_size
        self.full_audio_size = full_audio_size
        self.model = model
        self.input = input
        self.audio = input.audio_batch
        self.num_samples = input.num_samples

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

        delta_frames = int(self.chunk_size // self.model.encoder_frame_2_audio_samples)

        full_encoder_frames = int(
            self.full_audio_size / self.model.encoder_frame_2_audio_samples
        )

        encoder_contexts = torch.zeros(
            [
                encoder_output.shape[0],
                full_encoder_frames // 2,
                encoder_output.shape[2],
            ],
            dtype=encoder_output.dtype,
            device=encoder_output.device,
        )
        encoder_context_lens = torch.zeros(
            [self.input.audio_batch.shape[0]], dtype=torch.int64
        ).to(encoder_output.device)

        full_windows: list[bool] = []
        absolute_window_curss: list[int] = []
        absolute_context_curss: list[int] = []
        absolute_finalize_curss: list[int] = []
        finalized_hyps: list[Hypothesis | None] = []
        finalized_decoder_states: list[LabelLoopingStateItem | None] = []

        for i, p in enumerate(prev_states):
            abs_context_curs = 0 if p is None else p.abs_context_cursor
            abs_window_start_curs = 0 if p is None else p.abs_window_start_cursor
            abs_finalize_curs = 0 if p is None else p.abs_finalize_curs
            full_window = False if p is None else p.full_window
            finalized_hyp = None
            finalized_decoder_state = None

            # move the cursors
            if abs_context_curs >= full_encoder_frames - 1:
                full_window = True
            if full_window:
                abs_window_start_curs += delta_frames

            abs_context_curs += delta_frames

            absolute_context_curss.append(abs_context_curs)
            absolute_window_curss.append(abs_window_start_curs)
            full_windows.append(full_window)

            delta_finalized = abs_context_curs - abs_finalize_curs
            if delta_finalized >= full_encoder_frames // 2:
                abs_finalize_curs = abs_context_curs
                delta_finalized = 0
                finalized_hyp = p.latest_hyp if p is not None else None
                finalized_decoder_state = (
                    p.latest_decoder_state if p is not None else None
                )

            finalized_hyps.append(finalized_hyp)
            finalized_decoder_states.append(finalized_decoder_state)

            absolute_finalize_curss.append(abs_finalize_curs)

            abs_start_curs = abs_context_curs - delta_finalized

            relative_start_curs = (
                abs_start_curs - abs_window_start_curs
            ) % full_encoder_frames
            relative_context_curs = (
                abs_context_curs - abs_window_start_curs
            ) % full_encoder_frames

            encoder_contexts[i, : (relative_context_curs - relative_start_curs), :] = (
                encoder_output[i, relative_start_curs:relative_context_curs, :]
            )
            encoder_context_lens[i] = relative_context_curs - relative_start_curs

            print(
                "NEIL absolute_context_curs",
                abs_context_curs,
                abs_window_start_curs,
                relative_start_curs,
                relative_context_curs,
                relative_context_curs - relative_start_curs,
                full_encoder_frames,
                encoder_output_len,
            )

        return InternalEncodeResult(
            encoder_contexts=encoder_contexts,
            encoder_context_lens=encoder_context_lens,
            absolute_window_curss=absolute_window_curss,
            absolute_context_curss=absolute_context_curss,
            absolute_finalize_curss=absolute_finalize_curss,
            finalized_decoder_states=finalized_decoder_states,
            finalized_hyps=finalized_hyps,
            full_windows=full_windows,
        )

    def decode(self, encode_result: "InternalEncodeResult"):
        batched_state = None
        if any(ds is not None for ds in encode_result.finalized_decoder_states):
            batched_state = self.model.decoder.merge_to_batched_state(
                [ds for ds in encode_result.finalized_decoder_states]
            )

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
        for i, h in enumerate(split_hypotheses):
            assert isinstance(h, Hypothesis)
            txt = self.model.encoder.tokenizer.ids_to_text(h.y_sequence.tolist())
            print("NEIL txt", txt)


@dataclass
class InternalEncodeResult:
    encoder_contexts: torch.Tensor
    encoder_context_lens: torch.Tensor
    absolute_window_curss: list[int]
    absolute_context_curss: list[int]
    absolute_finalize_curss: list[int]
    finalized_hyps: list[Hypothesis | None]
    finalized_decoder_states: list[LabelLoopingStateItem | None]
    full_windows: list[bool]


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


@dataclass
class ParakeetSTTInferenceState:
    abs_context_cursor: int
    abs_window_start_cursor: int
    abs_finalize_curs: int
    full_window: bool
    latest_hyp: Hypothesis | None
    latest_decoder_state: LabelLoopingStateItem | None
