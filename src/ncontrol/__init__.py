"""N Control: one scalar control for deterministic traversal of N-D parameter spaces."""
from .core import ParameterAxis, SerpentineTraversal
from .named import NamedParameter, NamedParameterSpace
from .tk import NDimensionalKnob

__all__ = [
    "ParameterAxis",
    "SerpentineTraversal",
    "NamedParameter",
    "NamedParameterSpace",
    "NDimensionalKnob",
]

__version__ = "0.1.0"
