"""
Constants used throughout the Ares Engine project.
"""

import sys

# Required Python version as (major, minor)
# This is the single source of truth for Python version requirements
REQUIRED_PYTHON_VERSION = (3, 12)

# Platform detection
platform = sys.platform
PLATFORM_WINDOWS = "Windows"
PLATFORM_MACOS = "MacOS" 
PLATFORM_LINUX = "Linux"

CURRENT_PLATFORM = (PLATFORM_WINDOWS if platform.startswith("win") else 
                    PLATFORM_MACOS if platform.startswith("darwin") else 
                    PLATFORM_LINUX)
