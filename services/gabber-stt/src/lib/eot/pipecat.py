import threading

import numpy as np
import onnxruntime
from transformers import WhisperFeatureExtractor

from .eot import EOTInference

DEFAULT_MODEL_PATH = "./weights/smart-turn-v3.0.onnx"
CHUNK_SECONDS = 8


class PipeCatEOTInference(EOTInference):
    def __init__(self, *, model_path: str = DEFAULT_MODEL_PATH):
        super().__init__()
        self._model_path = model_path
        self._feature_extractor = WhisperFeatureExtractor(chunk_length=CHUNK_SECONDS)
        self._init_thread = threading.Thread(target=self._initialize_onnx)
        self._init_thread.start()
        self._init_evt = threading.Event()

    def _initialize_onnx(self):
        opts = onnxruntime.SessionOptions()
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        opts.intra_op_num_threads = 8
        opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL

        self._onnx_session = onnxruntime.InferenceSession(
            self._model_path,
            providers=["CPUExecutionProvider"],
            sess_options=opts,
        )
        self._init_evt.set()

    def inference(self, audio_chunks: np.typing.NDArray[np.int16]) -> list[float]:
        try:
            self._init_thread.join(10)
        except RuntimeError as e:
            raise RuntimeError("Failed to initialize VAD model") from e

        if not self._init_evt.is_set():
            raise RuntimeError("VAD model initialization timed out")

        if audio_chunks.shape[1] != self.chunk_size:
            raise ValueError(
                f"Invalid audio chunk size: {audio_chunks.shape[1]}, expected {self.chunk_size}"
            )

        batch = audio_chunks.astype(np.float32) / 32768.0

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
        return results

    @property
    def sample_rate(self) -> int:
        return 16000

    @property
    def chunk_size(self) -> int:
        return self._feature_extractor.chunk_length * self.sample_rate
