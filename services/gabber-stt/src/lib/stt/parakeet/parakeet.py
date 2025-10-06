import asyncio
import threading

import torch
from core import AudioInferenceRequest, AudioInferenceInternalResult

from ..stt import STTInference, STTInferenceResult
from .model import CanaryModelInstance, load_model
from nemo.collections.asr.parts.utils.rnnt_utils import (
    BatchedHyps,
    batched_hyps_to_hypotheses,
)
from nemo.collections.asr.parts.submodules.transducer_decoding.label_looping_base import (
    BatchedLabelLoopingState,
)
from nemo.collections.asr.parts.utils.rnnt_utils import Hypothesis


# High level strategy comes from:
# https://github.com/NVIDIA-NeMo/NeMo/blob/main/examples/asr/asr_chunked_inference/rnnt/speech_to_text_streaming_infer_rnnt.py
class ParakeetSTTInference(STTInference):
    def __init__(
        self,
        *,
        left_context_secs: float = 20.0,
        chunk_secs: float = 0.25,
    ):
        self._left_context_secs = left_context_secs
        self._chunk_secs = chunk_secs

        self._model: CanaryModelInstance | None = None

    @property
    def sample_rate(self) -> int:
        return 16000

    @property
    def new_audio_size(self) -> int:
        return int(self.sample_rate * self._chunk_secs)

    @property
    def full_audio_size(self) -> int:
        return int(self.sample_rate * (self._left_context_secs + self._chunk_secs))

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

        new_encoder_features = int(
            self._model.encoder_features_per_sec * self._chunk_secs
        )
        print(
            "NEIL got encoder_output",
            encoder_output.shape,
            encoder_output_len,
            encoder_output_len.shape,
            new_encoder_features,
        )
        decode_out_len = torch.div(
            encoder_output_len, new_encoder_features, rounding_mode="floor"
        )

        encoder_context = encoder_output[:, :-new_encoder_features, :]

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
            split_states = split_state(state)
            for i, none_idx in enumerate(no_state_idxs):
                new_states[none_idx] = split_states[i]

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
                with_state_batch[i, :] = encoder_context[with_idx, :]

            combined_state = combine_states(
                [input.prev_states[i] for i in with_state_idxs]
            )
            chunk_batched_hyps, _, state = self._model.decoder(
                x=with_state_batch,
                out_len=decode_out_len,
                prev_batched_state=combined_state,
            )
            split_states = split_state(state)
            for i, with_idx in enumerate(with_state_idxs):
                new_states[with_idx] = split_states[i]
            hyp = batched_hyps_to_hypotheses(
                chunk_batched_hyps, None, batch_size=chunk_batched_hyps.batch_size
            )
            print("NEIL got hyp with state", hyp)
            for i, with_idx in enumerate(with_state_idxs):
                hypotheses[with_idx] = hyp[i]

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
                    state=new_states[i],
                )
            )

        return results


# @dataclass
# class BatchedLabelLoopingState:
#     """Decoding state to pass between invocations"""


#     predictor_states: Any
#     predictor_outputs: torch.Tensor
#     labels: torch.Tensor
#     decoded_lengths: torch.Tensor
#     lm_states: Optional[torch.Tensor] = None
#     time_jumps: Optional[torch.Tensor] = None
def combine_states(states: list[BatchedLabelLoopingState]) -> BatchedLabelLoopingState:
    assert len(states) > 0
    res = states[0]
    for s in states[1:]:
        res.decoded_lengths = torch.cat((res.decoded_lengths, s.decoded_lengths), dim=0)
        res.predictor_outputs = torch.cat(
            (res.predictor_outputs, s.predictor_outputs), dim=0
        )

        res.predictor_states = (
            torch.cat((res.predictor_states[0], s.predictor_states[0]), dim=0),
            torch.cat((res.predictor_states[1], s.predictor_states[1]), dim=0),
        )

        res.labels = torch.cat((res.labels, s.labels), dim=0)
    return res


def split_state(state: BatchedLabelLoopingState) -> list[BatchedLabelLoopingState]:
    res: list[BatchedLabelLoopingState] = []
    for i in range(state.decoded_lengths.shape[0]):
        res.append(
            BatchedLabelLoopingState(
                decoded_lengths=state.decoded_lengths[i : i + 1],
                predictor_outputs=state.predictor_outputs[i : i + 1],
                predictor_states=(
                    state.predictor_states[0][i : i + 1],
                    state.predictor_states[1][i : i + 1],
                ),
                labels=state.labels[i : i + 1],
                time_jumps=state.time_jumps,
            )
        )
    return res
