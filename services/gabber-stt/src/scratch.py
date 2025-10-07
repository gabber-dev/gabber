import asyncio
import base64
import copy
import logging
import threading
import uuid
from dataclasses import dataclass, field

import aiohttp
import lightning.pytorch as pl
import numpy as np
import pyaudio
import torch
import wave
from nemo.collections.asr.models import ASRModel
from nemo.collections.asr.parts.submodules.rnnt_decoding import RNNTDecodingConfig
from nemo.collections.asr.parts.submodules.transducer_decoding.label_looping_base import (
    GreedyBatchedLabelLoopingComputerBase,
)
from nemo.collections.asr.parts.utils.streaming_utils import (
    AudioBatch,
    ContextSize,
    SimpleAudioDataset,
    StreamingBatchedAudioBuffer,
)
from nemo.collections.asr.parts.utils.rnnt_utils import (
    BatchedHyps,
    batched_hyps_to_hypotheses,
)
from nemo.collections.asr.parts.utils.transcribe_utils import setup_model
from omegaconf import OmegaConf, open_dict
import queue
from nemo.collections.asr.parts.utils.timestamp_utils import process_timestamp_outputs
from nemo.collections.asr.models import EncDecHybridRNNTCTCModel, EncDecRNNTModel

CHUNK = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


def make_divisible_by(num, factor: int) -> int:
    """Make num divisible by factor"""
    return (num // factor) * factor


@dataclass
class TranscriptionConfig:
    model_path: str | None = None
    pretrained_name: str | None = None
    audio_dir: str | None = None
    dataset_manifest: str | None = None
    output_filename: str | None = None
    batch_size: int = 32
    num_workers: int = 0
    append_pred: bool = False
    pred_name_postfix: str | None = None
    random_seed: int | None = None
    chunk_secs: float = 0.2
    left_context_secs: float = 10.0
    right_context_secs: float = 0.2
    cuda: int | None = None
    allow_mps: bool = True  # allow to select MPS device (Apple Silicon M-series GPU)
    compute_dtype: str | None = None
    matmul_precision: str = "high"
    audio_type: str = "wav"
    overwrite_transcripts: bool = True
    decoding: RNNTDecodingConfig = field(default_factory=RNNTDecodingConfig)
    timestamps: bool = False
    calculate_wer: bool = True
    clean_groundtruth_text: bool = False
    langid: str = "en"
    use_cer: bool = False


p = pyaudio.PyAudio()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
cfg = OmegaConf.structured(
    TranscriptionConfig(pretrained_name="nvidia/parakeet-tdt-0.6b-v3")
)
model, _ = setup_model(cfg=cfg, map_location=device)
model_cfg = copy.deepcopy(model._cfg)
OmegaConf.set_struct(model_cfg.preprocessor, False)
model_cfg.preprocessor.dither = 0.0
model_cfg.preprocessor.pad_to = 0

if model_cfg.preprocessor.normalize != "per_feature":
    logging.error(
        "Only EncDecRNNTBPEModel models trained with per_feature normalization are supported currently"
    )

OmegaConf.set_struct(model_cfg.preprocessor, True)

model.freeze()
model = model.to(device)
model.to(torch.float16)

with open_dict(cfg.decoding):
    if (
        cfg.decoding.strategy != "greedy_batch"
        or cfg.decoding.greedy.loop_labels is not True
    ):
        raise NotImplementedError(
            "This script currently supports only `greedy_batch` strategy with Label-Looping algorithm"
        )
    cfg.decoding.tdt_include_token_duration = cfg.timestamps
    cfg.decoding.greedy.preserve_alignments = False
    cfg.decoding.fused_batch_size = -1  # temporarily stop fused batch during inference.
    cfg.decoding.beam.return_best_hypothesis = (
        True  # return and write the best hypothsis only
    )

if hasattr(model, "change_decoding_strategy"):
    print("NEIL decoding strategy")
    if not isinstance(model, EncDecRNNTModel) and not isinstance(
        model, EncDecHybridRNNTCTCModel
    ):
        raise ValueError(
            "The script supports rnnt model and hybrid model with rnnt decodng!"
        )
    else:
        # rnnt model
        if isinstance(model, EncDecRNNTModel):
            model.change_decoding_strategy(cfg.decoding)

        # hybrid ctc rnnt model with decoder_type = rnnt
        if hasattr(model, "cur_decoder"):
            model.change_decoding_strategy(cfg.decoding, decoder_type="rnnt")

model.preprocessor.featurizer.dither = 0.0
model.preprocessor.featurizer.pad_to = 0
model.eval()

decoding_computer: GreedyBatchedLabelLoopingComputerBase = (
    model.decoding.decoding.decoding_computer
)

audio_sample_rate = RATE

feature_stride_sec = model_cfg.preprocessor["window_stride"]
features_per_sec = 1.0 / feature_stride_sec
encoder_subsampling_factor = model.encoder.subsampling_factor

features_frame2audio_samples = make_divisible_by(
    int(audio_sample_rate * feature_stride_sec), factor=encoder_subsampling_factor
)
encoder_frame2audio_samples = features_frame2audio_samples * encoder_subsampling_factor
print("NEIL encoder frame to audio", encoder_frame2audio_samples)


class TestClient:
    def __init__(self):
        self._stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        self._input_queue = queue.Queue[bytes]()

    def _stream_thread(self):
        while True:
            data = self._stream.read(CHUNK, exception_on_overflow=False)
            self._input_queue.put(data)

    def run(self):
        print("NEIL running")
        thread = threading.Thread(target=self._stream_thread)
        thread.start()

        state = None

        with torch.no_grad(), torch.inference_mode():
            while True:
                data = self._input_queue.get()
                audio_batch = (
                    torch.frombuffer(data, dtype=torch.int16).to(torch.float16)
                    / 32768.0
                )
                audio_batch = audio_batch.unsqueeze(0).to(device)
                input_signal_length = (
                    torch.Tensor([audio_batch.shape[1]]).to(torch.float16).to(device)
                )
                encoder_output, encoder_output_len = model(
                    input_signal=audio_batch,
                    input_signal_length=input_signal_length,
                )
                encoder_output = encoder_output.transpose(1, 2)
                CNT = 1
                delta = int(encoder_output_len / CNT)
                for i in range(CNT):
                    encoder_context = encoder_output[:, i * delta : (i + 1) * delta]
                    print(
                        "NEIL got encoder_output",
                        encoder_context.shape,
                        encoder_output.shape,
                    )
                    chunk_batched_hyps, _, state = decoding_computer(
                        x=encoder_context,
                        out_len=torch.Tensor([encoder_context.shape[1]]),
                        prev_batched_state=state,
                    )
                    hyp = batched_hyps_to_hypotheses(
                        chunk_batched_hyps, None, batch_size=1
                    )
                    if hyp[0].y_sequence.shape[0] > 0:
                        txt = (model.tokenizer.ids_to_text(hyp[0].y_sequence),)
                        print("NEIL got y_sequence", txt)
                # hyp.text = model.tokenizer.ids_to_text(hyp)
                # hyp = model.decoding.compute_rnnt_timestamps(hyp)
                # hyp = process_timestamp_outputs(
                #     hyp,
                #     subsampling_factor=model.encoder.subsampling_factor,
                #     window_stride=model.cfg["preprocessor"]["window_stride"],
                # )

                # print("NEIL got output", chunk_batched_hyps, hyp.text, hyp)


if __name__ == "__main__":
    tc = TestClient()
    tc.run()
