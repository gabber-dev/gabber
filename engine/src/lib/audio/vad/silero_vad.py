# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
import os
import threading
from typing import Optional

import numpy as np
import onnxruntime

SUPPORTED_SAMPLE_RATE = 16000
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WEIGHTS_PATH = os.path.join(SCRIPT_DIR, "files", "silero_vad.onnx")

VAD_CHUNK_SIZE = 512
VAD_STATE_SHAPE = (2, 1, 128)
PCM_16_NORMALIZATION_FACTOR = 32768.0


onnxruntime.set_default_logger_severity(3)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SileroVAD:
    def __init__(self):
        self._sess: Optional[onnxruntime.InferenceSession] = None
        self._state = np.zeros(VAD_STATE_SHAPE).astype(np.float32)
        self._init_lock = threading.Lock()
        self._initialized = False

    def _lazy_init(self):
        """Initialize ONNX session lazily to avoid blocking the main thread"""
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            try:
                logger.info(f"Initializing VAD engine with model: {WEIGHTS_PATH}")
                opts = onnxruntime.SessionOptions()
                opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
                opts.add_session_config_entry("session.inter_op.allow_spinning", "0")
                opts.inter_op_num_threads = 1
                opts.intra_op_num_threads = 1
                opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL

                self._sess = onnxruntime.InferenceSession(
                    WEIGHTS_PATH, providers=["CPUExecutionProvider"], sess_options=opts
                )
                self._initialized = True
                logger.info("VAD engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize VAD engine: {e}")
                # Don't raise - let the node fall back to passthrough mode

    def reset_states(self):
        """Reset VAD model states"""
        self._state = np.zeros(VAD_STATE_SHAPE).astype(np.float32)

    def inference(self, audio_chunk: np.ndarray) -> float:
        """Run VAD inference on audio chunk
        Args:
            audio_chunk: numpy array of audio samples (512 samples, float32, normalized to [-1, 1])
        Returns:
            VAD probability score (0.0 to 1.0)
        """
        if not self._initialized:
            self._lazy_init()

        if not self._initialized or self._sess is None:
            logger.warning("VAD engine not initialized, returning 0.0")
            return 0.0

        try:
            if audio_chunk.shape[0] != VAD_CHUNK_SIZE:
                logger.warning(
                    f"Invalid audio chunk size: {audio_chunk.shape[0]}, expected {VAD_CHUNK_SIZE}"
                )
                return 0.0

            if audio_chunk.ndim == 1:
                audio_chunk = np.expand_dims(audio_chunk, axis=0)

            ort_inputs = {
                "input": audio_chunk,
                "state": self._state,
                "sr": np.array(SUPPORTED_SAMPLE_RATE, dtype=np.int64),
            }
            ort_outputs = self._sess.run(None, ort_inputs)
            out, self._state = ort_outputs
            vad_score = float(out.item())

            return vad_score
        except Exception as e:
            logger.error(f"VAD inference error: {e}")
            return 0.0
