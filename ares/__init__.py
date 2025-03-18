"""
Ares Engine: A cross-platform game engine with Cython acceleration.
"""

from __future__ import annotations

# Package version
__version__ = "0.1.0"

# Import core components for direct access
from ares.core import Window, Input

# Define what gets imported with "from ares import *"
__all__ = [
    # Core components
    'Window', 'Input',
    
    # Package metadata
    '__version__'
]
