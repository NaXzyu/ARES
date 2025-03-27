"""
Utility module for the Ares Engine.

This module provides various utility functions and classes used throughout the engine.
"""

from __future__ import annotations

from .log import Log
from .build_utils import compute_file_hash, find_main_script
from .constants import REQUIRED_PYTHON_VERSION, PLATFORM_WINDOWS, PLATFORM_MACOS, PLATFORM_LINUX, CURRENT_PLATFORM
from .paths import USER_CONFIG_DIR, USER_DATA_DIR, USER_LOGS_DIR, USER_SCREENSHOTS_DIR, USER_SAVES_DIR

__all__ = [
    'Log',
    'compute_file_hash',
    'find_main_script',
    'REQUIRED_PYTHON_VERSION',
    'PLATFORM_WINDOWS',
    'PLATFORM_MACOS',
    'PLATFORM_LINUX',
    'CURRENT_PLATFORM',
    'USER_CONFIG_DIR',
    'USER_DATA_DIR',
    'USER_LOGS_DIR',
    'USER_SCREENSHOTS_DIR',
    'USER_SAVES_DIR',
]
