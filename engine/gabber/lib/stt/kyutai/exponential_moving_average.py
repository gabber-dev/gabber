# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import numpy as np


class ExponentialMovingAverage:
    def __init__(
        self, attack_time: float, release_time: float, initial_value: float = 0.0
    ):
        """An EMA that can smooth differently for attack (up) and release (down).

        Args:
            attack_time: Time in seconds to reach 50% of the target value.
                Used when the new value is greater than the current value.
            release_time: Time in seconds to decay to 50% of the target value.
                Used when the new value is less than the current value.
            initial_value: Initial value of the EMA.
        """
        self.attack_time = attack_time
        self.release_time = release_time
        self.value = initial_value

    def update(self, *, dt: float, new_value: float) -> float:
        assert dt > 0.0, f"dt must be positive, got {dt=}"
        assert new_value >= 0.0, f"new_value must be non-negative, got {new_value=}"

        if new_value > self.value:
            alpha = 1 - np.exp(-dt / self.attack_time * np.log(2))
        else:
            alpha = 1 - np.exp(-dt / self.release_time * np.log(2))

        self.value = float((1 - alpha) * self.value + alpha * new_value)
        return self.value

    def time_to_decay_to(self, value: float) -> float:
        """Return the time in seconds it will take for the estimate to reach `value`
        if it started at 1."""
        assert 0 < value < 1
        return float(-self.release_time * np.log2(value))
