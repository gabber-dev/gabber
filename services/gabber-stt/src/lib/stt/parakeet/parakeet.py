import asyncio
from itertools import batched
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

        torch_audio_batch = (
            torch.from_numpy(input.audio_batch).to(torch.float32) / 32768.0
        ).to(self._model.encoder.device)
        input_signal_length = torch.Tensor([torch_audio_batch.shape[1]]).to(
            self._model.encoder.device
        )

        encoder_output, encoder_output_len = self._model.encoder(
            input_signal=torch_audio_batch,
            input_signal_length=input_signal_length,
        )

        encoder_output = encoder_output.transpose(1, 2)

        # encoder_context = encoder_output[:, self.left_context_encoder_frames :, :]
        encoder_context = encoder_output

        no_state_idxs: list[int] = []
        with_state_idxs: list[int] = []
        for i, inp in enumerate(input.prev_states):
            if inp is None:
                no_state_idxs.append(i)
            else:
                with_state_idxs.append(i)

        decode_results = self.decode_batch(
            encoder_features=encoder_context,
            batch_idxs=no_state_idxs,
        )

        results: list[AudioInferenceInternalResult[STTInferenceResult]] = []
        for i, dr in enumerate(decode_results):
            converted_words = [
                STTInferenceResultWord(
                    word=w.text,
                    start_cursor=w.start_offset,
                    end_cursor=w.end_offset,
                )
                for w in dr.words
            ]
            results.append(
                AudioInferenceInternalResult(
                    result=STTInferenceResult(
                        transcription=dr.transcription,
                        start_cursor=0,
                        end_cursor=0,
                        words=converted_words,
                    ),
                    state=None,
                )
            )

        return results

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

        result: list[DecodeResult] = []
        for h in split_hypotheses:
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
                )
            )

        return result


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
