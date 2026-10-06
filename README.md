# N Control

**N Control** lets one dial, slider, automation lane, or scalar value navigate an arbitrarily large N-dimensional parameter space.

It uses a reversible mixed-radix serpentine traversal that preserves locality: consecutive scalar positions map to neighboring lattice states, changing exactly one parameter by exactly one discrete step. This makes enormous parameter spaces practical to browse without the disruptive jumps produced by ordinary mixed-radix counting.

N Control is designed as a reusable primitive for synthesizers, procedural generation, simulations, optimization and search, generative art, game tools, scientific parameter sweeps, and any interface where many parameters need to be explored through one compact control. Named parameter spaces let applications keep semantic names such as `melody.pitch`, `filter.cutoff`, or `material.roughness` while retaining the same reversible scalar traversal.

## Install

From GitHub:

```bash
pip install git+https://github.com/Matthew81975/n-control.git
```

After a PyPI release:

```bash
pip install n-control
```

## Basic use

```python
from ncontrol import ParameterAxis, SerpentineTraversal

space = SerpentineTraversal((
    ParameterAxis(20.0, 20_000.0, 100),
    ParameterAxis(0.0, 1.0, 101),
    ParameterAxis(0.0, 360.0, 73),
))

index = 12_345
frequency, amplitude, phase = space.values(index)

# One normalized UI control can address the complete N-D lattice.
index = space.from_normalized(0.42)
values = space.values(index)
```

## Named parameter spaces

N Control can also preserve semantic parameter names and metadata:

```python
from ncontrol import NamedParameterSpace

synth = NamedParameterSpace({
    "osc.frequency": {
        "minimum": 20.0,
        "maximum": 20_000.0,
        "steps": 100,
        "unit": "Hz",
    },
    "osc.amplitude": {
        "minimum": 0.0,
        "maximum": 1.0,
        "steps": 101,
    },
    "filter.cutoff": {
        "minimum": 20.0,
        "maximum": 20_000.0,
        "steps": 100,
        "unit": "Hz",
    },
})

state = synth.values(synth.from_normalized(0.42))
print(state["osc.frequency"])
```

Names can be hierarchical (`melody.pitch`, `instrument.filter.cutoff`, etc.), which makes the same control primitive reusable across large composed systems.


## Probabilistic state spaces

N Control can also treat every dimension as a state space with a probability distribution and constraints. States may be literal values or opaque pointers to procedures, materials, nested controls, or other registry objects.

```python
from ncontrol import BinaryConstraint, PointerState, ProbabilisticNControl, StateSpace

rooms = StateSpace(["kitchen", "bedroom"])
appliances = StateSpace([
    PointerState("appliance.oven", "Oven"),
    PointerState("appliance.lamp", "Lamp"),
])

control = ProbabilisticNControl({"room": rooms, "appliance": appliances})
result = control.collapse_all()
```

Weights express preference; constraints express possibility. Constraint pruning automatically renormalizes surviving weights. The framework exposes entropy and minimum-entropy collapse, so Wave Function Collapse is one policy over the same general N-Control representation rather than a separate subsystem.

## Why serpentine traversal?

A naive mixed-radix counter jumps when one digit rolls over. N Control reflects each nested sub-grid on alternating rows, producing a generalized boustrophedon path. For every pair of consecutive states, the Manhattan distance in lattice coordinates is exactly 1.

The traversal is:

- deterministic
- bijective
- reversible
- framework-independent
- dependency-free
- arbitrary-dimensional
- compatible with a dial, slider, automation lane, random walk, or optimizer

## API

```python
ParameterAxis(minimum, maximum, steps)
SerpentineTraversal(axes)
NamedParameter(minimum, maximum, steps, unit=None, description=None)
NamedParameterSpace(parameters)
```

Important traversal methods:

```python
space.digits(index)          # lattice coordinate tuple
space.index(digits)          # coordinate -> scalar index
space.values(index)          # real parameter values
space.nearest_index(values)  # real values -> nearest state
space.normalized(index)      # index -> [0, 1]
space.from_normalized(t)     # [0, 1] -> index
```

## Origin

N Control was extracted from the Genesis Forge tooling, where it was developed to navigate very large procedural parameter spaces with a single persistent control.

## License

MIT


## Tk widget

N Control also ships with an optional Tk rotary control:

```python
from ncontrol import NDimensionalKnob

knob = NDimensionalKnob(
    parent,
    maximum=space.count - 1,
    value=0,
    command=on_change,
    tk=tk,
    ttk=ttk,
    auto_scan_enabled=False,  # keep Auto Scan capability but disable it in this app
)
```

`auto_scan_enabled` defaults to `True`. Setting it to `False` disables the Auto Scan UI and behavior without removing Auto Scan from the reusable control.
