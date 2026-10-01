"""N Control: one scalar control for deterministic traversal of N-D parameter spaces."""
from .core import ParameterAxis, SerpentineTraversal
from .named import NamedParameter, NamedParameterSpace

__all__ = [
    "ParameterAxis",
    "SerpentineTraversal",
    "NamedParameter",
    "NamedParameterSpace",
]

__version__ = "0.1.0"
