import threading

import torch
from nemo.collections.asr.models import ASRModel
import numpy as np
from typing import Any

from ..stt import STT, STTInference, STTInternalInferenceResult, STTInferenceRequest
from .model import CanaryModelInstance, load_model


# High level strategy comes from:
# https://github.com/NVIDIA-NeMo/NeMo/blob/main/examples/asr/asr_chunked_inference/rnnt/speech_to_text_streaming_infer_rnnt.py
class ParakeetSTTInference(STTInference):
    def __init__(
        self,
        *,
        left_context_secs: float = 20.0,
        right_context_secs: float = 0.2,
        chunk_secs: float = 0.2,
    ):
        self._left_context_secs = left_context_secs
        self._right_context_secs = right_context_secs
        self._chunk_secs = chunk_secs
        self._init_thread = threading.Thread(target=self._initialize_model)
        self._init_thread.start()
        self._init_evt = threading.Event()
        self._model: CanaryModelInstance | None = None

    @property
    def sample_rate(self) -> int:
        return 16000

    @property
    def new_audio_size(self) -> int:
        return int(self.sample_rate * self._chunk_secs)

    @property
    def left_context_size(self) -> int:
        return int(self.sample_rate * self._left_context_secs)

    @property
    def right_context_size(self) -> int:
        return int(self.sample_rate * self._right_context_secs)

    def _initialize_model(self):
        self._model = load_model()

    def inference(self, input: STTInferenceRequest) -> list[STTInternalInferenceResult]:
        try:
            self._init_thread.join(10)
        except RuntimeError as e:
            raise RuntimeError("Failed to initialize VAD model") from e

        if not self._init_evt.is_set():
            raise RuntimeError("VAD model initialization timed out")

        assert self._model is not None

        if input.audio_batch.shape[1] != self.new_audio_size:
            raise ValueError(
                f"Invalid audio size: {input.audio_batch.shape[1]}, must be multiple of {self.new_audio_size}"
            )

        torch_audio_batch = (
            torch.from_numpy(input.audio_batch).to(torch.float16) / 32768.0
        ).to(self._model.encoder.device)
        input_signal_length = (
            torch.Tensor([torch_audio_batch.shape[1]])
            .to(torch.float16)
            .to(self._model.encoder.device)
        )

        encoder_output, encoder_output_len = self._model.encoder(
            input_signal=torch_audio_batch,
            input_signal_length=input_signal_length,
        )
        chunk_batched_hyps, _, state = self._model.decoder(
            x=encoder_output,
            out_len=encoder_output_len,
            prev_batched_state=None,
        )

        print("NEIL DEBUG chunk_batched_hyps:", chunk_batched_hyps)

        return []
