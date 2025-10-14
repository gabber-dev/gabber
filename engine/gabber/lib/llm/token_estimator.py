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
        text_chars_per_token: float,
    ):
        self._image_pixels_per_token = image_pixels_per_token
        self._video_frame_pixels_per_token = video_frame_pixels_per_token
        self._audio_samples_per_token = audio_samples_per_token
        self._text_chars_per_token = text_chars_per_token

    def estimate_tokens_for_content_item(self, item: ContextMessageContentItem) -> int:
        if isinstance(item, ContextMessageContentItem_Text):
            return max(1, int(len(item.content) / self._text_chars_per_token))
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

            return max(0, int(pixels / self._video_frame_pixels_per_token))
        elif isinstance(item, (ContextMessageContentItem_Image)):
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
    video_frame_pixels_per_token=1024 * 1024 / 3,
    image_pixels_per_token=1024 * 1024 / 3,
    audio_samples_per_token=16000,
    text_chars_per_token=4,
)

QWEN_TOKEN_ESTIMATOR = TokenEstimator(
    video_frame_pixels_per_token=2048,
    image_pixels_per_token=4096,
    audio_samples_per_token=16000,
    text_chars_per_token=4,
)

DEFAULT_TOKEN_ESTIMATOR = OPENAI_TOKEN_ESTIMATOR
