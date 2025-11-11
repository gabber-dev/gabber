# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import os
import threading

import numpy as np
import torch
import torchaudio
import onnxruntime
from .lipsync import LipSyncInference, Viseme, VisemeProability, LipSyncResult
from core import AudioInferenceRequest, AudioInferenceInternalResult

SUPPORTED_SAMPLE_RATE = 16000
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WEIGHTS_PATH = os.path.join("weights", "openlipsync.onnx")

FFT_HOP_SIZE = 160
FFT_WINDOW_SIZE = 400
N_MELS = 80
N_FFT = 1024
F_MIN = 50
F_MAX = 6000
INFERENCE_WINDOW_SIZE = 32000
INFERENCE_DELTA_SIZE = 160


onnxruntime.set_default_logger_severity(3)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

mel_spectrogram_transform = torchaudio.transforms.MelSpectrogram(
    sample_rate=SUPPORTED_SAMPLE_RATE,
    n_fft=N_FFT,
    hop_length=FFT_HOP_SIZE,
    win_length=FFT_WINDOW_SIZE,
    n_mels=N_MELS,
    f_max=F_MAX,
    f_min=F_MIN,
    power=2.0,
    normalized=False,
)
db_transform = torchaudio.transforms.AmplitudeToDB("power", top_db=80)


class OpenLipSyncInference(LipSyncInference):
    def __init__(self, *, model_path: str = DEFAULT_WEIGHTS_PATH):
        logger.info(f"Initializing LipSync engine with model: {model_path}")
        self._model_path = model_path
        self._onnx_session: onnxruntime.InferenceSession | None = None

    def _initialize_onnx(self):
        opts = onnxruntime.SessionOptions()
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        opts.add_session_config_entry("session.inter_op.allow_spinning", "0")
        opts.graph_optimization_level = (
            onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        )
        opts.intra_op_num_threads = 4
        opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL

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
        return INFERENCE_WINDOW_SIZE

    @property
    def new_audio_size(self) -> int:
        return INFERENCE_DELTA_SIZE

    @property
    def sample_rate(self) -> int:
        return SUPPORTED_SAMPLE_RATE

    def inference(
        self, input: AudioInferenceRequest
    ) -> list[AudioInferenceInternalResult[list[LipSyncResult]]]:
        audio_chunks = input.audio_batch
        if self._onnx_session is None:
            logger.warning("LipSync ONNX session is not initialized")
            return [
                AudioInferenceInternalResult[list[LipSyncResult]](state=None, result=[])
            ]

        if audio_chunks.ndim == 1:
            audio_chunks = np.expand_dims(audio_chunks, axis=0)

        if audio_chunks.shape[1] != INFERENCE_WINDOW_SIZE:
            raise ValueError(
                f"Invalid audio chunk size: {audio_chunks.shape[1]}, expected {INFERENCE_WINDOW_SIZE}"
            )

        audio_float = torch.from_numpy(audio_chunks.astype(np.float32) / 32768.0)

        mels = mel_spectrogram_transform(audio_float)
        mels_db = db_transform(mels)
        mels_db = mels_db.transpose(1, 2)

        results: list[list[LipSyncResult]] = []

        # TODO, this is slow, the published onnx model is not exported with batch inference. export with batch support to speed this up.
        try:
            for i in range(mels_db.shape[0]):
                ort_inputs = {
                    "audio_features": mels_db.numpy()[i : i + 1, :, :],
                }
                ort_outs = self._onnx_session.run(None, ort_inputs)
                torch_outs = torch.from_numpy(ort_outs[0])
                probs = torch.softmax(torch_outs, dim=-1)

                max_indxs = torch.argmax(probs, dim=-1).numpy()
                res: list[LipSyncResult] = []
                for time_idx in range(probs.shape[1]):
                    result = LipSyncResult(
                        max_viseme_prob=VisemeProability(
                            viseme=Viseme(max_indxs[0, time_idx]),
                            probability=probs[
                                0, time_idx, max_indxs[0, time_idx]
                            ].item(),
                        ),
                        start_sample=time_idx * FFT_HOP_SIZE,
                        end_sample=time_idx * FFT_HOP_SIZE + FFT_WINDOW_SIZE,
                    )
                    res.append(result)

                results.append(res)

            return [
                AudioInferenceInternalResult[list[LipSyncResult]](
                    state=None, result=results[i]
                )
                for i in range(len(results))
            ]
        except Exception as e:
            logger.error(f"LipSync inference failed: {e}")

        self._onnx_session = None
        self._initialize_onnx()
        return [
            AudioInferenceInternalResult[list[LipSyncResult]](state=None, result=[])
            for _ in range(audio_chunks.shape[0])
        ]
