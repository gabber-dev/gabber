from .audio_frame import AudioFrame
from .virtual_device import VirtualDevice


class VirtualMicrophone(VirtualDevice[AudioFrame]):
    def __init__(self, *, channels: int, sample_rate: int):
        self.channels = channels
        self.sample_rate = sample_rate
        super().__init__()

    def push(self, item: AudioFrame):
        if item.num_channels != self.channels:
            raise ValueError(
                f"AudioFrame has {item.num_channels} channels, expected {self.channels}"
            )

        if item.sample_rate != self.sample_rate:
            raise ValueError(
                f"AudioFrame has sample rate {item.sample_rate}, expected {self.sample_rate}"
            )

        super().push(item)
