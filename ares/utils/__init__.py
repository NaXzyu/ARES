"""
Utility functions for the Ares Engine.
"""

from __future__ import annotations

# Import constants
from .constants import *

# Import utility functions
from .utils import format_size, format_time

# Define what gets imported with "from ares.utils import *"
__all__ = [
    # Constants
    'REQUIRED_PYTHON_VERSION',
    'APP_NAME', 'PROJECT_ROOT', 'VENV_DIR', 'SOURCE_DIR', 'BUILD_DIR',
    'CONFIG_DIR', 'CONFIG_FILES_DIR', 'BUILD_SCRIPT', 'RES_DIR', 'DIST_DIR',
    'PLATFORM_WINDOWS', 'PLATFORM_MACOS', 'PLATFORM_LINUX', 'CURRENT_PLATFORM',
    'USER_DATA_DIR', 'USER_CONFIG_DIR', 'USER_LOGS_DIR', 'USER_SCREENSHOTS_DIR',
    'USER_SAVES_DIR',
    
    # Utility functions
    'format_size', 'format_time', 
    'detect_existing_venv', 'ensure_venv_active', 'get_venv_python'
]
