"""Named, self-describing parameter spaces built on N Control."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any

from .core import ParameterAxis, SerpentineTraversal


@dataclass(frozen=True, slots=True)
class NamedParameter:
    """Metadata for one named axis in a parameter space."""

    minimum: float
    maximum: float
    steps: int
    unit: str | None = None
    description: str | None = None

    def axis(self) -> ParameterAxis:
        return ParameterAxis(self.minimum, self.maximum, self.steps)


class NamedParameterSpace:
    """An ordered dictionary-like named N-D space with scalar traversal control.

    Parameter names are preserved in all mapping-oriented APIs, so callers can
    work with semantic names instead of remembering positional vector indices.
    """

    def __init__(self, parameters: Mapping[str, NamedParameter | Mapping[str, Any]]):
        if not parameters:
            raise ValueError("parameter space requires at least one parameter")

        parsed: dict[str, NamedParameter] = {}
        for name, spec in parameters.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("parameter names must be non-empty strings")
            if isinstance(spec, NamedParameter):
                parameter = spec
            elif isinstance(spec, Mapping):
                parameter = NamedParameter(**spec)
            else:
                raise TypeError("parameter specifications must be NamedParameter or mappings")
            parsed[name] = parameter

        self.parameters = parsed
        self.names = tuple(parsed)
        self.traversal = SerpentineTraversal(parameter.axis() for parameter in parsed.values())
        self.count = self.traversal.count

    def values(self, index: int) -> dict[str, float]:
        return dict(zip(self.names, self.traversal.values(index)))

    def digits(self, index: int) -> dict[str, int]:
        return dict(zip(self.names, self.traversal.digits(index)))

    def nearest_index(self, values: Mapping[str, float]) -> int:
        self._require_names(values)
        return self.traversal.nearest_index(values[name] for name in self.names)

    def index(self, digits: Mapping[str, int]) -> int:
        self._require_names(digits)
        return self.traversal.index(digits[name] for name in self.names)

    def normalized(self, index: int) -> float:
        return self.traversal.normalized(index)

    def from_normalized(self, position: float) -> int:
        return self.traversal.from_normalized(position)

    def vector(self, values: Mapping[str, float]) -> tuple[float, ...]:
        self._require_names(values)
        return tuple(values[name] for name in self.names)

    def mapping(self, vector) -> dict[str, float]:
        vector = tuple(vector)
        if len(vector) != len(self.names):
            raise ValueError("vector dimensionality mismatch")
        return dict(zip(self.names, vector))

    def _require_names(self, mapping: Mapping[str, Any]) -> None:
        missing = [name for name in self.names if name not in mapping]
        extra = [name for name in mapping if name not in self.parameters]
        if missing or extra:
            parts = []
            if missing:
                parts.append(f"missing: {', '.join(missing)}")
            if extra:
                parts.append(f"unknown: {', '.join(extra)}")
            raise ValueError("parameter names do not match space (" + "; ".join(parts) + ")")
