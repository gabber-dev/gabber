from .video_frame import VideoFrame, VideoFormat
from .media_iterator import MediaIterator
from .virtual_device import VirtualDevice


class VirtualCamera(VirtualDevice[VideoFrame]):
    def __init__(self, *, format: VideoFormat, width: int, height: int) -> None:
        self.format = format
        self.width = width
        self.height = height

        self._iterators: list[MediaIterator[VideoFrame]] = []

    def push(self, item: VideoFrame):
        if item.format != self.format:
            raise ValueError(
                f"VideoFrame has format {item.format}, expected {self.format}"
            )

        if item.width != self.width or item.height != self.height:
            raise ValueError(
                f"VideoFrame has dimensions {item.width}x{item.height}, expected {self.width}x{self.height}"
            )

        super().push(item)
