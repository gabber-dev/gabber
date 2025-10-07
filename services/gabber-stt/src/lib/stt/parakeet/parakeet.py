import asyncio
import threading
from typing import Any, cast
from dataclasses import dataclass

import torch
from core import AudioInferenceInternalResult, AudioInferenceRequest
from nemo.collections.asr.parts.submodules.transducer_decoding.label_looping_base import (
    BatchedLabelLoopingState,
)
from nemo.collections.asr.parts.utils.rnnt_utils import (
    BatchedHyps,
    Hypothesis,
    batched_hyps_to_hypotheses,
)

from ..stt import STTInference, STTInferenceResult
from .model import CanaryModelInstance, load_model


# High level strategy comes from:
# https://github.com/NVIDIA-NeMo/NeMo/blob/main/examples/asr/asr_chunked_inference/rnnt/speech_to_text_streaming_infer_rnnt.py
class ParakeetSTTInference(STTInference):
    def __init__(
        self,
        *,
        left_context_secs: float = 20.0,
        chunk_secs: float = 1,
        right_context_secs: float = 0,
    ):
        self._left_context_secs = left_context_secs
        self._chunk_secs = chunk_secs
        self._right_context_secs = right_context_secs

        self._model: CanaryModelInstance | None = None

    @property
    def sample_rate(self) -> int:
        return 16000

    @property
    def new_audio_size(self) -> int:
        return int(self.sample_rate * self._chunk_secs)

    @property
    def full_audio_size(self) -> int:
        return int(
            self.sample_rate
            * (self._left_context_secs + self._chunk_secs + self._right_context_secs)
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
            raise ValueError(
                f"Invalid audio size: {input.audio_batch.shape[1]}, must be multiple of {self.new_audio_size}"
            )

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

        left_features = int(
            self._left_context_secs * self._model.encoder_features_per_sec
        )
        right_features = int(
            self._right_context_secs * self._model.encoder_features_per_sec
        )
        chunk_features = encoder_output_len - left_features - right_features

        decode_out_len = (
            torch.Tensor([chunk_features])
            .to(torch.int32)
            .to(self._model.encoder.device)
        )

        encoder_context = encoder_output[:, left_features:, :]

        print("NEIL", encoder_output.shape, encoder_context.shape)

        # For new sessions, we handle those inferences separately
        hypotheses: list[Hypothesis | None] = [None] * input.audio_batch.shape[0]
        new_states: list[BatchedLabelLoopingState | None] = [
            None
        ] * input.audio_batch.shape[0]

        no_state_idxs: list[int] = []
        with_state_idxs: list[int] = []
        for i, inp in enumerate(input.prev_states):
            if inp is None:
                no_state_idxs.append(i)
            else:
                with_state_idxs.append(i)

        if len(no_state_idxs) > 0:
            no_state_batch = (
                torch.zeros(len(no_state_idxs), *encoder_context.shape[1:])
                .to(encoder_context.device)
                .to(encoder_output.dtype)
            )
            for i, none_idx in enumerate(no_state_idxs):
                no_state_batch[i, :] = encoder_context[none_idx, :]

            chunk_batched_hyps, _, state = self._model.decoder(
                x=no_state_batch,
                out_len=decode_out_len,
                prev_batched_state=None,
            )
            split_states = self._model.decoder.split_batched_state(state)
            for i, none_idx in enumerate(no_state_idxs):
                new_states[none_idx] = cast(BatchedLabelLoopingState, split_states[i])

            hyp = batched_hyps_to_hypotheses(
                chunk_batched_hyps, None, batch_size=chunk_batched_hyps.batch_size
            )
            for i, none_idx in enumerate(no_state_idxs):
                hypotheses[none_idx] = hyp[i]

        if len(with_state_idxs) > 0:
            with_state_batch = (
                torch.zeros(len(with_state_idxs), *encoder_context.shape[1:])
                .to(encoder_context.device)
                .to(encoder_output.dtype)
            )
            for i, with_idx in enumerate(with_state_idxs):
                hypotheses[with_idx] = input.prev_states[with_idx].current_hyp
                with_state_batch[i, :] = encoder_context[with_idx, :]

            combined_state = self._model.decoder.merge_to_batched_state(
                [input.prev_states[i].decoder_state for i in with_state_idxs]
            )
            chunk_batched_hyps, _, state = self._model.decoder(
                x=with_state_batch,
                out_len=decode_out_len,
                prev_batched_state=combined_state,
            )
            split_states = self._model.decoder.split_batched_state(state)
            for i, with_idx in enumerate(with_state_idxs):
                new_states[with_idx] = cast(BatchedLabelLoopingState, split_states[i])
            hyp = batched_hyps_to_hypotheses(
                chunk_batched_hyps, None, batch_size=chunk_batched_hyps.batch_size
            )
            for i, with_idx in enumerate(with_state_idxs):
                curr_hyp = hypotheses[with_idx]
                assert curr_hyp is not None
                merged = curr_hyp.merge_(hyp[i])
                hypotheses[with_idx] = merged

        results: list[AudioInferenceInternalResult[STTInferenceResult]] = []
        for i, h in enumerate(hypotheses):
            if h is None:
                raise RuntimeError("Hypothesis should not be none here")
            text = self._model.encoder.tokenizer.ids_to_text(h.y_sequence)  # type: ignore
            print("NEIL text", text)
            results.append(
                AudioInferenceInternalResult(
                    result=STTInferenceResult(
                        transcription=text,
                        start_cursor=0,
                        end_cursor=0,
                        words=[],
                    ),
                    state=State(decoder_state=new_states[i], current_hyp=h),
                )
            )

        return results


@dataclass
class State:
    decoder_state: BatchedLabelLoopingState | None
    current_hyp: Hypothesis | None
