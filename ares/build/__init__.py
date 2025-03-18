"""
Build system for Ares Engine.

This package contains utilities for building, compiling, and packaging
the Ares Engine and its extensions.
"""

from __future__ import annotations

# Import the primary build functionalities
from .build_engine import build_engine, compute_file_hash, get_extensions
from .build_ext_ninja import BuildExtWithNinja

# Define what gets imported with "from ares.build import *"
__all__ = [
    # Build engine functions
    'build_engine',
    'get_extensions',
    'compute_file_hash',
    
    # Build extension classes
    'BuildExtWithNinja',
]
