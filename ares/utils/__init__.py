"""
Utility module for the Ares Engine.

This module provides various utility functions and classes used throughout the engine.
"""

from __future__ import annotations

from .log import Log, SimpleLogger, simple_logger
from .build_utils import compute_file_hash, find_main_script, get_cython_module_dirs

__all__ = [
    'Log',
    'SimpleLogger',
    'simple_logger',
    'compute_file_hash',
    'find_main_script',
    'get_cython_module_dirs',
]
