"""
Ares Engine - A cross-platform game engine with Cython acceleration.

Ares is a modern game engine designed for fast development and high performance.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Engine version
__version__ = "0.1.0"
__author__ = "k. rawson"

# Add the project root to the Python path if not already there
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Ensure config is initialized
from ares.config import initialize as _initialize_config
_initialize_config()

# Import commonly used modules for easier access
from ares.config import engine_config

__all__ = [
    '__version__',
    '__author__',
    'engine_config',
]

def __getattr__(name):
    if name == 'Window':
        from ares.core import Window
        return Window
    elif name == 'Input':
        from ares.core import Input
        return Input
    elif name == 'Renderer':
        from ares.renderer import Renderer
        return Renderer
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
