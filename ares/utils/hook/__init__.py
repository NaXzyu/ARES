"""PyInstaller hooks for the Ares Engine."""

from __future__ import annotations

from ares.utils.const import (
    REQUIRED_PYTHON_VERSION,
    REQUIRED_PYTHON_VERSION_STR,
    ARES_ENGINE_VERSION,
    ARES_ENGINE_VERSION_STR
)

from .hook_type import HookType
from .hook_manager import HookManager
from .configs_hook import init_configs
from .sdl2_hook import configure_sdl2_paths
from .ares_hook import (
    collect_ares_files, 
    get_ares_path, 
    hiddenimports
)
from .cython_hook import (
    ensure_directory_exists,
    create_init_file,
    load_binary_module
)
from .logging_hook import (
    setup_runtime_logging,
    handle_exception,
    LoggerWriter,
    dump_module_search_paths
)

__all__ = [
    'HookManager',
    'HookType',

    # Ares hooks
    'collect_ares_files',
    'get_ares_path',
    'hiddenimports',

    # Config hooks
    'init_configs',

    # Cython module hooks
    'create_init_file',
    'ensure_directory_exists',
    'load_binary_module',

    # Logging hooks
    'LoggerWriter',
    'dump_module_search_paths',
    'handle_exception',
    'setup_runtime_logging',

    # SDL2 hooks
    'configure_sdl2_paths',

    # Version constants
    'REQUIRED_PYTHON_VERSION',
    'REQUIRED_PYTHON_VERSION_STR',
    'ARES_ENGINE_VERSION',
    'ARES_ENGINE_VERSION_STR'
]
