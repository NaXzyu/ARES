"""
Ares Engine - A cross-platform game engine with Cython acceleration.

Ares is a modern game engine designed for fast development and high performance.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Engine version
__version__ = "0.1.0"
__author__ = "k. rawson"

# Add the project root to the Python path if not already there
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

__all__ = [
    '__version__',
    '__author__'
]
