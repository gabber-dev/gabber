import copy
import logging
from dataclasses import dataclass, field

import torch
from nemo.collections.asr.models import ASRModel
from nemo.collections.asr.parts.submodules.rnnt_decoding import (
    RNNTDecodingConfig,
)
from nemo.collections.asr.parts.submodules.transducer_decoding.label_looping_base import (
    GreedyBatchedLabelLoopingComputerBase,
)

from nemo.collections.asr.parts.utils.transcribe_utils import setup_model
from omegaconf import OmegaConf, open_dict
from nemo.collections.asr.models import EncDecHybridRNNTCTCModel, EncDecRNNTModel

MODEL_SAMPLE_RATE = 16000


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


def load_model():
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
        cfg.decoding.fused_batch_size = (
            -1
        )  # temporarily stop fused batch during inference.
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
                model.change_decoding_strategy(cfg.decoding, decoder_type="rnnt")  # type: ignore

    model.preprocessor.featurizer.dither = 0.0  # type: ignore
    model.preprocessor.featurizer.pad_to = 0  # type: ignore
    model.eval()

    decoder: GreedyBatchedLabelLoopingComputerBase = (
        model.decoding.decoding.decoding_computer  # type: ignore
    )

    feature_stride_sec = model_cfg.preprocessor["window_stride"]
    features_per_sec = 1.0 / feature_stride_sec
    encoder_subsampling_factor = model.encoder.subsampling_factor  # type: ignore

    features_frame2audio_samples = make_divisible_by(
        int(MODEL_SAMPLE_RATE * feature_stride_sec),
        factor=encoder_subsampling_factor,  # type: ignore
    )

    encoder_frame2audio_samples: int = (
        features_frame2audio_samples * encoder_subsampling_factor  # type: ignore
    )

    return CanaryModelInstance(
        encoder=model,
        audio_samples_per_encoder_frame=encoder_frame2audio_samples,
        decoder=decoder,
        features_per_sec=features_per_sec,
    )


@dataclass
class CanaryModelInstance:
    encoder: ASRModel
    decoder: GreedyBatchedLabelLoopingComputerBase
    audio_samples_per_encoder_frame: int
    features_per_sec: float
