# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
import os
import threading

import numpy as np
import onnxruntime
from .vad import VADInference

SUPPORTED_SAMPLE_RATE = 16000
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WEIGHTS_PATH = os.path.join(
    "../../engine/gabber/lib/audio/vad/files", "silero_vad.onnx"
)

VAD_CHUNK_SIZE = 512
PCM_16_NORMALIZATION_FACTOR = 32768.0


onnxruntime.set_default_logger_severity(3)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SileroVADInference(VADInference):
    def __init__(self, *, model_path: str = DEFAULT_WEIGHTS_PATH):
        logger.info(f"Initializing VAD engine with model: {model_path}")
        self._model_path = model_path

        self._init_thread = threading.Thread(target=self._initialize_onnx)
        self._init_thread.start()
        self._init_evt = threading.Event()

    def _initialize_onnx(self):
        opts = onnxruntime.SessionOptions()
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        opts.add_session_config_entry("session.inter_op.allow_spinning", "0")
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
        self._reset_states()

        self._onnx_session = onnxruntime.InferenceSession(
            self._model_path,
            providers=["CPUExecutionProvider"],
            sess_options=opts,
        )
        self._init_evt.set()

    @property
    def inference_chunk_sample_count(self) -> int:
        return VAD_CHUNK_SIZE

    @property
    def sample_rate(self) -> int:
        return SUPPORTED_SAMPLE_RATE

    def inference(self, audio_chunks: np.typing.NDArray[np.int16]) -> list[float]:
        try:
            self._init_thread.join(10)
        except RuntimeError as e:
            raise RuntimeError("Failed to initialize VAD model") from e

        if not self._init_evt.is_set():
            raise RuntimeError("VAD model initialization timed out")

        if audio_chunks.ndim == 1:
            audio_chunks = np.expand_dims(audio_chunks, axis=0)

        if audio_chunks.shape[1] != VAD_CHUNK_SIZE:
            raise ValueError(
                f"Invalid audio chunk size: {audio_chunks.shape[1]}, expected {VAD_CHUNK_SIZE}"
            )

        batch_size = audio_chunks.shape[0]
        if self._state.shape[1] != batch_size:
            self._reset_states(batch_size=batch_size)

        audio_batch = audio_chunks.astype(np.float32) / 32768.0

        sr_input = np.full((batch_size,), SUPPORTED_SAMPLE_RATE, dtype=np.int64)

        state_shape = list(self._state.shape)
        state_shape[1] = batch_size
        initial_state = np.zeros(state_shape, dtype=self._state.dtype)
        ort_inputs = {
            "input": audio_batch,
            "state": initial_state,
            "sr": sr_input,
        }
        print(
            "NEIL VAD ort_inputs",
            ort_inputs["input"].shape,
            ort_inputs["state"].shape,
            ort_inputs["sr"].shape,
        )
        ort_outputs = self._onnx_session.run(None, ort_inputs)
        out, _ = ort_outputs
        out_np = np.array(out)
        vad_scores = out_np[:, 0].astype(np.float32)
        return vad_scores.tolist()

    def _reset_states(self, *, batch_size: int = 1):
        self._state = np.zeros((2, batch_size, 128), dtype=np.float32)
