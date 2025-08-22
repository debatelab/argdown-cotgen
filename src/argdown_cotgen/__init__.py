"""
argdown-cotgen: Takes arbitrary argdown snippets and creates reasoning traces 
that mimic step by step reconstruction processes.
"""

from .core.generator import CotGenerator
from .core.models import CotStep, CotResult

__version__ = "0.1.0"
__all__ = ["CotGenerator", "CotStep", "CotResult"]
