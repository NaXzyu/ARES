"""
PyInstaller hooks for the Ares Engine.

These hooks ensure that all required modules and resources are included when freezing applications.
"""

from __future__ import annotations

# Import only what we need now - updated with new filenames
from .hook_type import HookType
from .hook_manager import HookManager

# Also import renamed hook files directly
from .configs_hook import init_configs
from .ares_hook import collect_ares_files, hiddenimports
from .sdl2_hook import configure_sdl2_paths

__all__ = [
    'HookType',
    'HookManager',
    'init_configs',
    'collect_ares_files',
    'hiddenimports',
    'configure_sdl2_paths'
]
