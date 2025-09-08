import numpy as np
from livekit import rtc


class AudioFrame:
    data: np.typing.NDArray[np.int16]  # (1,N) array of int16 PCM audio data
    sample_rate: int
    num_channels: int

    @staticmethod
    def from_numpy_array(array):
        pass

    @property
    def duration(self) -> float:
        if self.sample_rate <= 0 or self.num_channels <= 0:
            raise ValueError(
                "Sample rate and number of channels must be greater than zero."
            )
        total_samples = self.data.size  # Total elements in the array
        if total_samples == 0:
            return 0.0
        if total_samples % self.num_channels != 0:
            raise ValueError(
                "Data size must not divisible by num_channels—possible data corruption."
            )
        return float(self.data.size) / float(self.sample_rate * self.num_channels)

    def to_livekit_audio_frame(self) -> "rtc.AudioFrame":
        return rtc.AudioFrame(
            sample_rate=self.sample_rate,
            samples_per_channel=self.data.size // self.num_channels,
            num_channels=self.num_channels,
            data=self.data.tobytes(),
        )
