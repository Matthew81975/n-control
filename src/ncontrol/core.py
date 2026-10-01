"""Framework-independent one-dimensional control of N-D parameter lattices."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


@dataclass(frozen=True, slots=True)
class ParameterAxis:
    """One discretized bounded dimension in an N-dimensional parameter lattice."""

    minimum: float
    maximum: float
    steps: int

    def __post_init__(self) -> None:
        if not all(math.isfinite(v) for v in (self.minimum, self.maximum)):
            raise ValueError("axis bounds must be finite")
        if self.maximum < self.minimum:
            raise ValueError("axis maximum must be >= minimum")
        if type(self.steps) is not int or self.steps < 2:
            raise ValueError("axis steps must be an integer >= 2")

    def value(self, digit: int) -> float:
        if type(digit) is not int or not 0 <= digit < self.steps:
            raise ValueError("axis digit outside range")
        return self.minimum + (self.maximum - self.minimum) * digit / (self.steps - 1)

    def nearest_digit(self, value: float) -> int:
        if not math.isfinite(value):
            raise ValueError("axis value must be finite")
        if self.maximum == self.minimum:
            return 0
        t = (
            min(self.maximum, max(self.minimum, value)) - self.minimum
        ) / (self.maximum - self.minimum)
        return int(round(t * (self.steps - 1)))


class SerpentineTraversal:
    """Bijective mixed-radix snake traversal through an N-D lattice.

    Consecutive indices always differ by exactly one lattice step along exactly
    one axis. This generalizes a 2-D boustrophedon (snake) scan to arbitrary
    dimensionality while remaining exactly reversible.
    """

    def __init__(self, axes: Iterable[ParameterAxis]):
        self.axes = tuple(axes)
        if not self.axes or any(not isinstance(axis, ParameterAxis) for axis in self.axes):
            raise ValueError("traversal requires at least one ParameterAxis")
        self.count = math.prod(axis.steps for axis in self.axes)

    def digits(self, index: int) -> tuple[int, ...]:
        if type(index) is not int or not 0 <= index < self.count:
            raise ValueError("index outside traversal")

        def decode(axes: Sequence[ParameterAxis], position: int) -> tuple[int, ...]:
            if len(axes) == 1:
                return (position,)
            tail_count = math.prod(axis.steps for axis in axes[1:])
            head, tail = divmod(position, tail_count)
            if head & 1:
                tail = tail_count - 1 - tail
            return (head,) + decode(axes[1:], tail)

        return decode(self.axes, index)

    def index(self, digits: Iterable[int]) -> int:
        digits = tuple(digits)
        if len(digits) != len(self.axes):
            raise ValueError("digit dimensionality mismatch")
        for digit, axis in zip(digits, self.axes):
            if type(digit) is not int or not 0 <= digit < axis.steps:
                raise ValueError("axis digit outside range")

        def encode(axes: Sequence[ParameterAxis], ds: Sequence[int]) -> int:
            if len(axes) == 1:
                return ds[0]
            tail_count = math.prod(axis.steps for axis in axes[1:])
            tail = encode(axes[1:], ds[1:])
            if ds[0] & 1:
                tail = tail_count - 1 - tail
            return ds[0] * tail_count + tail

        return encode(self.axes, digits)

    def values(self, index: int) -> tuple[float, ...]:
        return tuple(
            axis.value(digit)
            for axis, digit in zip(self.axes, self.digits(index))
        )

    def nearest_index(self, values: Iterable[float]) -> int:
        values = tuple(values)
        if len(values) != len(self.axes):
            raise ValueError("value dimensionality mismatch")
        return self.index(
            tuple(axis.nearest_digit(value) for axis, value in zip(self.axes, values))
        )

    def normalized(self, index: int) -> float:
        if type(index) is not int or not 0 <= index < self.count:
            raise ValueError("index outside traversal")
        if self.count == 1:
            return 0.0
        return index / (self.count - 1)

    def from_normalized(self, position: float) -> int:
        if not math.isfinite(position) or not 0 <= position <= 1:
            raise ValueError("normalized position must be in [0, 1]")
        return int(round(position * (self.count - 1)))
