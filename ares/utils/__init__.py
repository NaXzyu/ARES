"""Utility modules for the Ares Engine."""

from __future__ import annotations

from .log import log
from .const import (
    REQUIRED_PYTHON_VERSION,
    PLATFORM_WINDOWS,
    PLATFORM_MACOS,
    PLATFORM_LINUX,
    CURRENT_PLATFORM,
    DEFAULT_LOG_FORMAT,
    DEFAULT_DATE_FORMAT,
    KB, MB, GB,
    DEFAULT_ENGINE_NAME,
)

from .paths import Paths, paths
from .build.build_utils import BuildUtils

__all__ = [
    # Utilities
    'log',
    'Paths',
    'paths',
    'BuildUtils',
    
    # Constants
    'REQUIRED_PYTHON_VERSION',
    'PLATFORM_WINDOWS',
    'PLATFORM_MACOS',
    'PLATFORM_LINUX',
    'CURRENT_PLATFORM',
    'DEFAULT_LOG_FORMAT',
    'DEFAULT_DATE_FORMAT',
    'KB', 'MB', 'GB',
    'DEFAULT_ENGINE_NAME',
]