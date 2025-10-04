import threading

import torch
from nemo.collections.asr.models import ASRModel

from ..stt import STT, STTInference, STTInferenceInput, STTInferenceResult
from .model import CanaryModelInstance, load_model


class CanarySTTInference(STTInference):
    def __init__(
        self,
        *,
        chunk_secs: float = 0.2,
    ):
        self._chunk_secs = chunk_secs
        self._init_thread = threading.Thread(target=self._initialize_model)
        self._init_thread.start()
        self._init_evt = threading.Event()
        self._model: CanaryModelInstance | None = None

    @property
    def sample_rate(self) -> int:
        return 16000

    @property
    def chunk_size(self) -> int:
        return int(self.sample_rate * self._chunk_secs)

    def _initialize_model(self):
        self._model = load_model()

    def inference(self, input: STTInferenceInput) -> STTInferenceResult:
        try:
            self._init_thread.join(10)
        except RuntimeError as e:
            raise RuntimeError("Failed to initialize VAD model") from e

        if not self._init_evt.is_set():
            raise RuntimeError("VAD model initialization timed out")

        assert self._model is not None

        audio_batch = (
            torch.frombuffer(input.audio_batch, dtype=torch.int16).to(torch.float16)
            / 32768.0
        ).to(self._model.encoder.device)
        input_signal_length = (
            torch.Tensor([audio_batch.shape[1]])
            .to(torch.float16)
            .to(self._model.encoder.device)
        )

        encoder_output, encoder_output_len = self._model.encoder(
            input_signal=audio_batch,
            input_signal_length=input_signal_length,
        )
        chunk_batched_hyps, _, state = self._model.decoder(
            x=encoder_output,
            out_len=encoder_output_len,
            prev_batched_state=None,
        )
