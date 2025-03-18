"""
Core engine functionality for window management and input handling.
"""

from __future__ import annotations

# Import primary components
from .window import Window
from .input import Input

# Define what gets imported with "from ares.core import *"
__all__ = [
    'Window',
    'Input'
]
