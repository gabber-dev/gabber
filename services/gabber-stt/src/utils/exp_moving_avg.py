import numpy as np


class ExponentialMovingAverage:
    def __init__(
        self, attack_time: float, release_time: float, initial_value: float = 0.0
    ):
        self.attack_time = attack_time
        self.release_time = release_time
        self.value = initial_value

    def update(self, *, dt: float, new_value: float) -> float:
        if new_value > self.value:
            alpha = 1 - np.exp(-dt / self.attack_time * np.log(2))
        else:
            alpha = 1 - np.exp(-dt / self.release_time * np.log(2))

        self.value = float((1 - alpha) * self.value + alpha * new_value)
        return self.value

    def time_to_decay_to(self, value: float) -> float:
        assert 0 < value < 1
        return float(-self.release_time * np.log2(value))
