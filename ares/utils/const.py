"""Constants used throughout the Ares Engine project."""

import sys

# Python version requirement
REQUIRED_PYTHON_VERSION = (3, 12)
REQUIRED_PYTHON_VERSION_STR = ".".join(map(str, REQUIRED_PYTHON_VERSION))

# Version constants
ARES_ENGINE_VERSION = (0, 1, 0) # Major, Minor, Patch
ARES_ENGINE_VERSION_STR = ".".join(map(str, ARES_ENGINE_VERSION))

# Platform detection
platform = sys.platform
PLATFORM_WINDOWS = "Windows"
PLATFORM_MACOS = "MacOS" 
PLATFORM_LINUX = "Linux"

CURRENT_PLATFORM = (PLATFORM_WINDOWS if platform.startswith("win") else 
                    PLATFORM_MACOS if platform.startswith("darwin") else 
                    PLATFORM_LINUX)

# Logging constants
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y.%m.%d:%H:%M:%S"

# File extension constants
PYD_EXTENSION = '.pyd'
SO_EXTENSION = '.so'
PYTHON_EXT = '.py'
C_EXTENSION = '.c'
WHEEL_EXTENSION = '.whl'
SDIST_EXTENSION = '.tar.gz'
SPEC_EXTENSION = '.spec'
EXE_SPEC_TEMPLATE = f"exe{SPEC_EXTENSION}"
PYX_EXTENSION = '.pyx'  # Cython source file
PXD_EXTENSION = '.pxd'  # Cython header file
PYTHON_TAG_PATTERN = "*.cp*-*"  # Python tag pattern for compiled modules

## Cython-related constants
ENGINE_WHEEL_PATTERN = "ares-*.whl"

# Common directory names
LOGS_DIR_NAME = "logs"
BUILD_DIR_NAME = "build"
CONFIG_DIR_NAME = "config"
CACHE_DIR_NAME = "cache"
ENGINE_DIR_NAME = "engine"
SCREENSHOTS_DIR_NAME = "Screenshots"
SAVE_GAMES_DIR_NAME = "SaveGames"
RESOURCES_DIR_NAME = "resources"

# Size constants (bytes)
KB = 1024
MB = 1024 * 1024
GB = 1024 * 1024 * 1024

# Default package name
DEFAULT_ENGINE_NAME = "AresEngine"
DEFAULT_CYTHON_MODULE_NAME = "ares_cython_modules"

# Build system constants
INVALID_COMPILER_FLAGS = ['common', 'unix', 'windows']
DEFAULT_COMPILER_DIRECTIVES = {
    'language_level': 3,
    'boundscheck': False,
    'wraparound': False,
    'cdivision': True,
}

# Status codes
SUCCESS = 0
ERROR_PYTHON_VERSION = 1
ERROR_MISSING_DEPENDENCY = 2
ERROR_INVALID_CONFIGURATION = 3
ERROR_BUILD_FAILED = 4
ERROR_RUNTIME = 5

# Script constants
SCRIPT_DEFAULT_TIMEOUT = 300  # Default timeout for script execution in seconds
SCRIPT_MAX_THREADS = 4        # Maximum number of threads for script execution
SCRIPT_LOG_PREFIX = "script_execution_"  # Prefix for script logs

# File specific constants
MAIN_SCRIPT_NAME = "main.py"
ENTRY_POINT_PATTERNS = ["if __name__ == '__main__':", 'if __name__ == "__main__":']
FILE_ENCODING = "utf-8"
FILE_CHUNK_SIZE = 4096 # Size of file chunks for reading/writing

# SDL2 constants
SDL2_DLL_SUBDIRS = ["sdl2dll/dll", "sdl2", "SDL2", "pysdl2"]
SDL2_DLL_DESTINATION = '.' # Destination for SDL2 DLLs

# Python cache directory name
PYCACHE_DIR_NAME = "__pycache__"

# Module extensions for various file types
MODULE_EXTENSIONS = [PYTHON_EXT, PYD_EXTENSION, SO_EXTENSION, '.ini']

# Directory names for various components
APP_CONFIG_DIR_NAME = "Config"
APP_LOGS_DIR_NAME = "Logs"
APP_CACHE_DIR_NAME = "Cache"
APP_DATA_DIR_NAME = "Data"
EXECUTABLE_OUTPUT_DIR_NAME = "out"
TEMP_DIR_NAME = "temp"
DIST_PATH_NAME = "dist"
HOOKS_PATH_NAME = "hooks"
INI_DIR_NAME = "ini"
CONFIG_INI_DIR_NAME = "config/ini"

# Default file names
DEFAULT_LOG_FILE = "engine.log"
BUILD_LOG_FILE = "build.log"
BUILD_CACHE_FILE = "build_cache.json"

# Default app and product names
DEFAULT_APP_NAME = "AresEngine"
DEFAULT_PRODUCT_NAME = "ares-engine"

# Path patterns and globs
WHEEL_SEARCH_PATTERN = "ares-*.whl"
SDIST_SEARCH_PATTERN = "*.tar.gz"
COMPILED_MODULE_PATTERNS = ["*.pyd", "*.so", "*.cp*-*.pyd", "*.cpython-*.so"]

# Directory structure constants
ARES_CHILD_PATH = "ares"
CORE_SUBDIR = "core"
MATH_SUBDIR = "math" 
PHYSICS_SUBDIR = "physics"
RENDERER_SUBDIR = "renderer"
UTILS_SUBDIR = "utils"
SPEC_CHILD_PATH = "utils/spec"

# Engine builder constants
ENGINE_BUILDER_WHEEL_COMMAND = ["wheel", ".", "-w"]
ENGINE_BUILD_SOURCE_COMMAND = ["sdist"]
ENGINE_SOURCE_PACKAGE_NAME = "ares"
SETUP_FILE_NAME = "setup.py"

# Build log section headers
BUILD_LOG_WHEEL_HEADER = "Wheel Build Output"
BUILD_LOG_CYTHON_HEADER = "Cython Compilation Output"
BUILD_LOG_SDIST_HEADER = "Source Distribution Output"
