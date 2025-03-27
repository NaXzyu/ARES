"""
Constants used throughout the Ares Engine project.
"""

import sys

# Only keep what's needed for version checking
REQUIRED_PYTHON_VERSION = (3, 12)

# Platform detection
platform = sys.platform
PLATFORM_WINDOWS = "Windows"
PLATFORM_MACOS = "MacOS" 
PLATFORM_LINUX = "Linux"

CURRENT_PLATFORM = (PLATFORM_WINDOWS if platform.startswith("win") else 
                    PLATFORM_MACOS if platform.startswith("darwin") else 
                    PLATFORM_LINUX)
