# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import os
import threading
import queue
from typing import Optional, Tuple

import numpy as np
import onnxruntime
import time

SUPPORTED_SAMPLE_RATE = 16000
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WEIGHTS_PATH = os.path.join(
    SCRIPT_DIR, "../../../engine/gabber/lib/audio/vad/files", "silero_vad.onnx"
)

VAD_CHUNK_SIZE = 512
VAD_STATE_SHAPE = (2, 1, 128)
PCM_16_NORMALIZATION_FACTOR = 32768.0


onnxruntime.set_default_logger_severity(3)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Silero:
    def __init__(
        self, *, model_path: str = DEFAULT_WEIGHTS_PATH, loop_delta_seconds: float = 0.1
    ):
        self._model_path = model_path
        self._sess: Optional[onnxruntime.InferenceSession] = None
        self._state = np.zeros(VAD_STATE_SHAPE).astype(np.float32)
        self._init_lock = threading.Lock()
        self._initialized = False
        self._input_queue: queue.Queue[Tuple[asyncio.Future[float], np.ndarray]] = (
            queue.Queue()
        )
        self._closed = False
        self._lock = threading.Lock()

    def run(self):
        while not self._closed:
            all_inputs: list[Tuple[asyncio.Future[float], np.ndarray]] = []
            time.sleep(0.01)

    def create_session(self) -> "SileroSession":
        return SileroSession(vad=self)

    async def _has_voice(self, audio_chunk: np.typing.NDArray[np.int16]) -> float:
        fut = asyncio.Future[float]()
        self._input_queue.put((fut, audio_chunk))
        res = await asyncio.wait_for(fut, timeout=1.0)
        return res

    def _lazy_init(self):
        """Initialize ONNX session lazily to avoid blocking the main thread"""
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            try:
                logger.info(f"Initializing VAD engine with model: {self._model_path}")
                opts = onnxruntime.SessionOptions()
                opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
                opts.add_session_config_entry("session.inter_op.allow_spinning", "0")
                opts.inter_op_num_threads = 1
                opts.intra_op_num_threads = 1
                opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL

                self._sess = onnxruntime.InferenceSession(
                    self._model_path,
                    providers=["CPUExecutionProvider"],
                    sess_options=opts,
                )
                self._initialized = True
                logger.info("VAD engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize VAD engine: {e}")
                # Don't raise - let the node fall back to passthrough mode

    def reset_states(self):
        """Reset VAD model states"""
        self._state = np.zeros(VAD_STATE_SHAPE).astype(np.float32)

    def inference(self, audio_chunks: list[np.typing.NDArray[np.int16]]) -> list[float]:
        if not self._initialized:
            self._lazy_init()

        if not self._initialized or self._sess is None:
            logger.warning("VAD engine not initialized, returning empty array")
            return [0.0] * len(audio_chunks)

        try:
            batch_size = len(audio_chunks)
            if batch_size == 0:
                return []

            audio_chunks = [
                chunk.flatten() if chunk.ndim > 1 else chunk for chunk in audio_chunks
            ]

            audio_batch = np.stack(audio_chunks, axis=0)

            if audio_batch.shape[1] != VAD_CHUNK_SIZE:
                logger.warning(
                    f"Invalid audio chunk size: {audio_batch.shape[1]}, expected {VAD_CHUNK_SIZE}"
                )
                return [0.0] * batch_size

            audio_batch = audio_batch.astype(np.float32) / 32768.0

            sr_input = np.full((batch_size,), SUPPORTED_SAMPLE_RATE, dtype=np.int64)

            state_shape = list(self._state.shape)
            state_shape[1] = batch_size
            initial_state = np.zeros(state_shape, dtype=self._state.dtype)
            ort_inputs = {
                "input": audio_batch,
                "state": initial_state,
                "sr": sr_input,
            }
            ort_outputs = self._sess.run(None, ort_inputs)
            out, _ = ort_outputs
            out_np = np.array(out)
            vad_scores = out_np[:, 0].astype(np.float32)
            return vad_scores.tolist()
        except Exception as e:
            logger.error(f"VAD inference error: {e}")
            return [0.0] * len(audio_chunks)


class SileroSession:
    def __init__(self, *, vad: Silero):
        self._vad = vad
        self._window = np.zeros((0,), dtype=np.int16) * VAD_CHUNK_SIZE

    async def has_voice(self, audio_chunk: np.typing.NDArray[np.int16]) -> float:
        full_chunks: list[np.typing.NDArray[np.int16]] = []
        if len(audio_chunk) > VAD_CHUNK_SIZE:
            full_chunks = np.array_split(
                audio_chunk[: len(audio_chunk) // VAD_CHUNK_SIZE * VAD_CHUNK_SIZE],
                len(audio_chunk) // VAD_CHUNK_SIZE,
            )
        else:
            self._window = np.concatenate((self._window, audio_chunk), axis=0)
            self._window = self._window[-VAD_CHUNK_SIZE:]
            full_chunks = [self._window]

        results = await asyncio.gather(
            *[self._vad._has_voice(chunk) for chunk in full_chunks]
        )

        return max(results)
