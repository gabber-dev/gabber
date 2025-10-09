import asyncio
import threading

import numpy as np
import onnxruntime
from core.audio_inference import AudioInferenceInternalResult, AudioInferenceRequest
from transformers import WhisperFeatureExtractor

from .eot import EOTInference

DEFAULT_MODEL_PATH = "./weights/smart-turn-v3.0.onnx"
CHUNK_SECONDS = 8


class PipeCatEOTInference(EOTInference):
    def __init__(self, *, model_path: str = DEFAULT_MODEL_PATH):
        super().__init__()
        self._model_path = model_path
        self._feature_extractor = WhisperFeatureExtractor(chunk_length=CHUNK_SECONDS)

    def _initialize_onnx(self):
        opts = onnxruntime.SessionOptions()
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        opts.intra_op_num_threads = 8
        opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL

        self._onnx_session = onnxruntime.InferenceSession(
            self._model_path,
            providers=["CUDAExecutionProvider"],
            sess_options=opts,
        )

    async def initialize(self) -> None:
        init_thread = threading.Thread(target=self._initialize_onnx)
        init_thread.start()
        await asyncio.get_event_loop().run_in_executor(None, init_thread.join, 120)

    def inference(
        self, input: AudioInferenceRequest
    ) -> list[AudioInferenceInternalResult[float]]:
        if input.audio_batch.shape[1] != self.full_audio_size:
            raise ValueError(
                f"Invalid audio chunk size: {input.audio_batch.shape[1]}, expected {self.full_audio_size}"
            )

        batch = input.audio_batch.astype(np.float32) / 32768.0

        inputs = self._feature_extractor(
            batch,
            sampling_rate=16000,
            return_tensors="np",
            padding="max_length",
            max_length=CHUNK_SECONDS * 16000,
            truncation=True,
            do_normalize=True,
        )

        input_features = inputs.input_features.astype(np.float32)

        outputs = self._onnx_session.run(None, {"input_features": input_features})
        results = outputs[0].flatten().tolist()  # type: ignore
        print("EOT OUTPUTS:", results)
        return [AudioInferenceInternalResult(result=r, state=None) for r in results]

    @property
    def sample_rate(self) -> int:
        return 16000

    @property
    def new_audio_size(self) -> int:
        return int(16000 * 0.1)

    @property
    def full_audio_size(self) -> int:
        return CHUNK_SECONDS * 16000
