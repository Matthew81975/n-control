import math
import random
import pytest
from ncontrol.state import BinaryConstraint, PointerState, ProbabilisticNControl, StateSpace

def test_uniform_distribution_and_entropy():
    space = StateSpace(["a", "b", "c"])
    assert space.probabilities() == {"a": pytest.approx(1/3), "b": pytest.approx(1/3), "c": pytest.approx(1/3)}
    assert space.entropy == pytest.approx(math.log(3))

def test_weights_renormalize_after_constraint():
    space = StateSpace(["a", "b", "c"], {"a": 1, "b": 2, "c": 7})
    space.allow_only(["a", "c"])
    assert space.probabilities() == {"a": pytest.approx(0.125), "c": pytest.approx(0.875)}

def test_pointer_states_are_ordinary_states():
    wall = PointerState("wall.curved", "Curved wall")
    cave = PointerState("wall.cave", "Cave wall")
    space = StateSpace([wall, cave], {wall: 3, cave: 1})
    assert set(space.probabilities()) == {wall, cave}

def test_seeded_collapse_is_deterministic():
    a = StateSpace(range(4), {0: 1, 1: 2, 2: 3, 3: 4})
    b = StateSpace(range(4), {0: 1, 1: 2, 2: 3, 3: 4})
    assert a.collapse(rng=random.Random(42)) == b.collapse(rng=random.Random(42))

def test_constraint_propagation_prunes_domains():
    rooms = StateSpace(["kitchen", "bedroom"])
    appliances = StateSpace(["oven", "lamp", "bed"])
    control = ProbabilisticNControl(
        {"room": rooms, "appliance": appliances},
        [BinaryConstraint("room", "appliance", lambda room, appliance: {
            "kitchen": {"oven", "lamp"}, "bedroom": {"bed", "lamp"}
        }[room].__contains__(appliance))],
    )
    rooms.select("kitchen")
    control.propagate()
    assert appliances.admissible == ("oven", "lamp")

def test_minimum_entropy_dimension_collapses_first():
    broad = StateSpace(["a", "b", "c"])
    narrow = StateSpace([1, 2], {1: 99, 2: 1})
    control = ProbabilisticNControl({"broad": broad, "narrow": narrow})
    assert control.next_dimension() == "narrow"

def test_collapse_all_respects_compatibility():
    left = StateSpace(["A", "B"])
    right = StateSpace([1, 2])
    control = ProbabilisticNControl(
        {"left": left, "right": right},
        [BinaryConstraint("left", "right", lambda a, b: (a == "A") == (b == 1))],
    )
    result = control.collapse_all(rng=random.Random(7))
    assert (result["left"], result["right"]) in {("A", 1), ("B", 2)}

def test_impossible_constraint_does_not_destroy_previous_domain():
    space = StateSpace([1, 2, 3])
    with pytest.raises(ValueError):
        space.constrain(lambda _: False)
    assert space.admissible == (1, 2, 3)
