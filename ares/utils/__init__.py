"""Utility modules for the Ares Engine."""

from __future__ import annotations

from .log import log
from .paths import Paths, paths
from .utils import (
    format_size, 
    format_time, 
    is_windows, 
    is_macos, 
    is_linux,
    compute_file_hash,
    get_app_name,
)
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

__all__ = [
    # Utilities
    'log',
    'Paths',
    'paths',
    'format_size',
    'format_time',
    'is_windows',
    'is_macos', 
    'is_linux',
    'compute_file_hash',
    'get_app_name',
    
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