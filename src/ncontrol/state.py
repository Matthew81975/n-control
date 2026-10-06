"""Probabilistic state spaces for N Control."""
from __future__ import annotations
from collections.abc import Callable, Hashable, Iterable, Mapping
from dataclasses import dataclass
import math
import random
from typing import Any, Generic, TypeVar

T = TypeVar("T", bound=Hashable)

@dataclass(frozen=True, slots=True)
class PointerState:
    """A hashable opaque pointer to a procedure, material, nested control, etc."""
    target: Hashable
    label: str | None = None

class StateSpace(Generic[T]):
    """Finite weighted state space with reversible admissibility pruning."""
    def __init__(self, states: Iterable[T], weights: Mapping[T, float] | None = None):
        ordered = tuple(states)
        if not ordered:
            raise ValueError("state space requires at least one state")
        if len(set(ordered)) != len(ordered):
            raise ValueError("states must be unique and hashable")
        self.states = ordered
        self._base_weights = {
            state: self._validated_weight(1.0 if weights is None else weights.get(state, 1.0))
            for state in ordered
        }
        if not any(self._base_weights.values()):
            raise ValueError("at least one state must have positive weight")
        self._allowed = set(ordered)
        self.selected: T | None = None

    @staticmethod
    def _validated_weight(value: float) -> float:
        value = float(value)
        if not math.isfinite(value) or value < 0:
            raise ValueError("weights must be finite and >= 0")
        return value

    @property
    def admissible(self) -> tuple[T, ...]:
        return tuple(state for state in self.states if state in self._allowed)

    @property
    def collapsed(self) -> bool:
        return len(self._allowed) == 1

    def weights(self) -> dict[T, float]:
        return {state: self._base_weights[state] for state in self.admissible}

    def probabilities(self) -> dict[T, float]:
        weights = self.weights()
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("admissible states have zero total probability")
        return {state: weight / total for state, weight in weights.items()}

    @property
    def entropy(self) -> float:
        return -sum(p * math.log(p) for p in self.probabilities().values() if p > 0)

    def set_weight(self, state: T, weight: float) -> None:
        self._require_state(state)
        self._base_weights[state] = self._validated_weight(weight)

    def constrain(self, predicate: Callable[[T], bool]) -> bool:
        before = set(self._allowed)
        self._allowed = {state for state in self._allowed if predicate(state)}
        if not self._allowed:
            self._allowed = before
            raise ValueError("constraint would eliminate every state")
        if self.selected not in self._allowed:
            self.selected = None
        return before != self._allowed

    def allow_only(self, states: Iterable[T]) -> bool:
        allowed = set(states)
        return self.constrain(lambda state: state in allowed)

    def reset(self) -> None:
        self._allowed = set(self.states)
        self.selected = None

    def collapse(self, *, rng: random.Random | None = None) -> T:
        if self.collapsed:
            state = self.admissible[0]
        else:
            rng = rng or random
            probabilities = self.probabilities()
            candidates = tuple(probabilities)
            state = rng.choices(candidates, weights=[probabilities[s] for s in candidates], k=1)[0]
            self._allowed = {state}
        self.selected = state
        return state

    def select(self, state: T) -> T:
        self._require_state(state)
        if state not in self._allowed:
            raise ValueError("state is not currently admissible")
        self._allowed = {state}
        self.selected = state
        return state

    def _require_state(self, state: T) -> None:
        if state not in self._base_weights:
            raise KeyError(state)

@dataclass(frozen=True, slots=True)
class BinaryConstraint:
    """Compatibility relation between two named state spaces."""
    left: str
    right: str
    compatible: Callable[[Any, Any], bool]

class ProbabilisticNControl:
    """Named state spaces plus constraint propagation and WFC-style collapse."""
    def __init__(self, dimensions: Mapping[str, StateSpace[Any]], constraints: Iterable[BinaryConstraint] = ()):
        if not dimensions:
            raise ValueError("N-control requires at least one dimension")
        self.dimensions = dict(dimensions)
        self.constraints = tuple(constraints)
        for constraint in self.constraints:
            if constraint.left not in self.dimensions or constraint.right not in self.dimensions:
                raise ValueError("constraint references unknown dimension")

    def propagate(self) -> None:
        changed = True
        while changed:
            changed = False
            for relation in self.constraints:
                left = self.dimensions[relation.left]
                right = self.dimensions[relation.right]
                right_states = right.admissible
                changed |= left.constrain(lambda a, rs=right_states, f=relation.compatible: any(f(a, b) for b in rs))
                left_states = left.admissible
                changed |= right.constrain(lambda b, ls=left_states, f=relation.compatible: any(f(a, b) for a in ls))

    def unresolved(self) -> tuple[str, ...]:
        return tuple(name for name, space in self.dimensions.items() if not space.collapsed)

    def next_dimension(self) -> str | None:
        unresolved = self.unresolved()
        if not unresolved:
            return None
        return min(unresolved, key=lambda name: self.dimensions[name].entropy)

    def collapse_next(self, *, rng: random.Random | None = None) -> tuple[str, Any] | None:
        self.propagate()
        name = self.next_dimension()
        if name is None:
            return None
        value = self.dimensions[name].collapse(rng=rng)
        self.propagate()
        return name, value

    def collapse_all(self, *, rng: random.Random | None = None) -> dict[str, Any]:
        while self.unresolved():
            self.collapse_next(rng=rng)
        return {name: space.admissible[0] for name, space in self.dimensions.items()}
