import logging
from gabber.core.runtime_types.types import (
    ContextMessage,
    ContextMessageContentItem,
    ContextMessageContentItem_Audio,
    ContextMessageContentItem_Video,
    ContextMessageContentItem_Text,
    ContextMessageContentItem_Image,
    ContextMessageRole,
)


class TokenEstimator:
    def __init__(
        self,
        *,
        video_frame_pixels_per_token: float,
        image_pixels_per_token: float,
        audio_samples_per_token: float,
        tokens_per_word: float,
    ):
        self._image_pixels_per_token = image_pixels_per_token
        self._video_frame_pixels_per_token = video_frame_pixels_per_token
        self._audio_samples_per_token = audio_samples_per_token
        self._tokens_per_words = tokens_per_word

    def estimate_tokens_for_content_item(self, item: ContextMessageContentItem) -> int:
        if isinstance(item, ContextMessageContentItem_Text):
            wordsish = item.content.split(" ")
            return int(len(wordsish) * self._tokens_per_words)
        elif isinstance(item, ContextMessageContentItem_Audio):
            total_dur = item.clip.duration
            if not total_dur or not item.clip.audio:
                return 0
            estimated_samples = int(
                total_dur * item.clip.audio[0].original_data.sample_rate
            )
            return int(estimated_samples / self._audio_samples_per_token)
        elif isinstance(item, ContextMessageContentItem_Video):
            pixels = 0
            for frame in item.clip.video:
                if frame.width and frame.height:
                    pixels += frame.width * frame.height
            if pixels == 0:
                return 0

            logging.info(f"NEIL Estimating tokens for image with {pixels} pixels")
            return max(0, int(pixels / self._video_frame_pixels_per_token))
        elif isinstance(item, (ContextMessageContentItem_Image)):
            pixels = item.frame.width * item.frame.height
            logging.info(f"NEIL Estimating tokens for image with {pixels} pixels")
            return max(
                1,
                int(
                    (item.frame.width * item.frame.height)
                    / self._image_pixels_per_token
                ),
            )
        else:
            return 0


OPENAI_TOKEN_ESTIMATOR = TokenEstimator(
    video_frame_pixels_per_token=32 * 32 / 2,
    image_pixels_per_token=32 * 32 / 2,
    audio_samples_per_token=16000,
    tokens_per_word=1.25,
)

QWEN_TOKEN_ESTIMATOR = TokenEstimator(
    video_frame_pixels_per_token=16 * 16,
    image_pixels_per_token=28 * 28,
    audio_samples_per_token=16000,
    tokens_per_word=1.25,
)

DEFAULT_TOKEN_ESTIMATOR = OPENAI_TOKEN_ESTIMATOR
