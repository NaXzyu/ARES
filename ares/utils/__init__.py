"""
Utility module for the Ares Engine.

This module provides various utility functions and classes used throughout the engine.
"""

from __future__ import annotations

from .log import Log
from .build_utils import compute_file_hash, find_main_script
from .constants import REQUIRED_PYTHON_VERSION, PLATFORM_WINDOWS, PLATFORM_MACOS, PLATFORM_LINUX, CURRENT_PLATFORM
from .paths import Paths, get_user_config_dir

# Initialize Paths and get commonly used directories
_paths = Paths()
_project_dirs = _paths.get_project_dirs()

# Export commonly used paths and flags
IS_FROZEN = Paths.IS_FROZEN
PROJECT_ROOT = _project_dirs["PROJECT_ROOT"]
BUILD_DIR = _project_dirs["BUILD_DIR"]
DEV_LOGS_DIR = _project_dirs["DEV_LOGS_DIR"]
ENGINE_BUILD_DIR = _project_dirs["ENGINE_BUILD_DIR"]

# Create user directories only when explicitly needed, not at import time
def _create_user_dirs():
    """Create and return user directories."""
    _user_dirs = _paths.create_app_directories()
    return {
        "USER_CONFIG_DIR": _user_dirs["CONFIG_DIR"],  
        "USER_DATA_DIR": _user_dirs["BASE_DIR"],
        "USER_LOGS_DIR": _user_dirs["LOGS_DIR"],
        "USER_SCREENSHOTS_DIR": _user_dirs["SCREENSHOTS_DIR"],
        "USER_SAVES_DIR": _user_dirs["SAVES_DIR"],
    }

# Export lazily loaded properties
USER_CONFIG_DIR = get_user_config_dir()  # This is safe to call and will not cause circular imports

# Add explicit functions for the other user directories
def get_user_data_dir():
    return _create_user_dirs()["USER_DATA_DIR"]

def get_user_logs_dir():
    return _create_user_dirs()["USER_LOGS_DIR"]

def get_user_screenshots_dir():
    return _create_user_dirs()["USER_SCREENSHOTS_DIR"]

def get_user_saves_dir():
    return _create_user_dirs()["USER_SAVES_DIR"]

__all__ = [
    'Log',
    'compute_file_hash',
    'find_main_script',
    'REQUIRED_PYTHON_VERSION',
    'PLATFORM_WINDOWS',
    'PLATFORM_MACOS',
    'PLATFORM_LINUX',
    'CURRENT_PLATFORM',
    'IS_FROZEN', 
    'PROJECT_ROOT',
    'BUILD_DIR',
    'DEV_LOGS_DIR',
    'ENGINE_BUILD_DIR',
    'USER_CONFIG_DIR',
    'get_user_config_dir',
    'get_user_data_dir',
    'get_user_logs_dir',
    'get_user_screenshots_dir',
    'get_user_saves_dir',
    'Paths',
]
