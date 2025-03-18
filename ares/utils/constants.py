"""
Constants used throughout the Ares Engine project.
"""

import os
import sys
from pathlib import Path

# Only keep what's needed for version checking
REQUIRED_PYTHON_VERSION = (3, 12)

# Application name
APP_NAME = "AresEngine"

# Platform detection
platform = sys.platform
PLATFORM_WINDOWS = "Windows"
PLATFORM_MACOS = "MacOS" 
PLATFORM_LINUX = "Linux"

CURRENT_PLATFORM = (PLATFORM_WINDOWS if platform.startswith("win") else 
                    PLATFORM_MACOS if platform.startswith("darwin") else 
                    PLATFORM_LINUX)

# User paths - platform specific directories for user data
if platform.startswith("win"):
    try:
        BASE_USER_PATH = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / "AppData" / "Local")))
    except (KeyError, TypeError):
        BASE_USER_PATH = Path.home() / "AppData" / "Local"
    USER_DATA_DIR = BASE_USER_PATH / APP_NAME / "Saved"
elif platform.startswith("darwin"):
    USER_DATA_DIR = Path.home() / "Library" / "Application Support" / APP_NAME / "Saved"
else:
    try:
        import appdirs
        USER_DATA_DIR = Path(appdirs.user_data_dir("ares-engine", APP_NAME)) / "Saved"
    except ImportError:
        USER_DATA_DIR = Path.home() / ".local" / "share" / "ares-engine" / "Saved"

# User directories
USER_CONFIG_DIR = USER_DATA_DIR / "Config" / CURRENT_PLATFORM
USER_LOGS_DIR = USER_DATA_DIR / "Logs"
USER_SCREENSHOTS_DIR = USER_DATA_DIR / "Screenshots"
USER_SAVES_DIR = USER_DATA_DIR / "SaveGames"
