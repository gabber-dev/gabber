from dataclasses import dataclass
from enum import Enum
import numpy as np

from livekit import rtc


class VideoFormat(Enum):
    RGBA = "RGBA"
    I420 = "I420"


@dataclass
class VideoFrame:
    data: np.ndarray  # (H,W,4) array of uint8 RGBA video data
    width: int
    height: int
    format: VideoFormat = VideoFormat.RGBA

    @classmethod
    def black_frame(cls, width: int, height: int, timestamp: float) -> "VideoFrame":
        """Create a black video frame of the given width and height."""
        data = np.zeros((height, width, 4), dtype=np.uint8)
        return cls(data=data, width=width, height=height)

    def to_livekit_video_frame(self) -> "rtc.VideoFrame":
        lk_format: rtc.VideoBufferType.ValueType

        if self.format == VideoFormat.RGBA:
            lk_format = rtc.VideoBufferType.RGBA
        elif self.format == VideoFormat.I420:
            lk_format = rtc.VideoBufferType.I420
        else:
            raise ValueError(f"Unsupported video format: {self.format}")

        return rtc.VideoFrame(
            type=lk_format,
            width=self.width,
            height=self.height,
            data=self.data.tobytes(),
        )
