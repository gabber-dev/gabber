# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import os
import threading

import numpy as np
import onnxruntime
from .vad import VADInference
from core import AudioInferenceRequest, AudioInferenceInternalResult

SUPPORTED_SAMPLE_RATE = 16000
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WEIGHTS_PATH = os.path.join(
    "../../engine/gabber/lib/audio/vad/files", "silero_vad.onnx"
)

CONTEXT_SIZE = 64
VAD_CHUNK_SIZE = 512


onnxruntime.set_default_logger_severity(3)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SileroVADInference(VADInference):
    def __init__(self, *, model_path: str = DEFAULT_WEIGHTS_PATH):
        logger.info(f"Initializing VAD engine with model: {model_path}")
        self._model_path = model_path
        self._onnx_session: onnxruntime.InferenceSession | None = None

    def _initialize_onnx(self):
        opts = onnxruntime.SessionOptions()
        opts.intra_op_num_threads = 4
        opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
        self._reset_states()

        self._onnx_session = onnxruntime.InferenceSession(
            self._model_path,
            providers=["CPUExecutionProvider"],
            sess_options=opts,
        )

    async def initialize(self) -> None:
        init_thread = threading.Thread(target=self._initialize_onnx)
        init_thread.start()
        await asyncio.get_event_loop().run_in_executor(None, init_thread.join, 10)
        if self._onnx_session is None:
            raise RuntimeError("VAD model initialization timed out")

    @property
    def full_audio_size(self) -> int:
        return VAD_CHUNK_SIZE

    @property
    def new_audio_size(self) -> int:
        return VAD_CHUNK_SIZE - CONTEXT_SIZE

    @property
    def sample_rate(self) -> int:
        return SUPPORTED_SAMPLE_RATE

    def inference(
        self, input: AudioInferenceRequest
    ) -> list[AudioInferenceInternalResult[float]]:
        print("NEIL VAD START")
        audio_chunks = input.audio_batch
        assert self._onnx_session is not None

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

        sr_input = np.array(SUPPORTED_SAMPLE_RATE, dtype=np.int64)

        ort_inputs = {
            "input": audio_batch,
            "state": self._state,
            "sr": sr_input,
        }

        ort_outputs = self._onnx_session.run(None, ort_inputs)
        out, _ = ort_outputs
        out_np = np.array(out)
        vad_scores = out_np[:, 0].astype(np.float32)
        print("NEIL VAD END")
        return [
            AudioInferenceInternalResult(result=score, state=None)
            for score in vad_scores
        ]

    def _reset_states(self, *, batch_size: int = 1):
        self._state = np.zeros((2, batch_size, 128), dtype=np.float32)
