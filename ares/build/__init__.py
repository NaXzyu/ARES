"""
Build system for the Ares Engine.

This module provides build tools and utilities for compiling and packaging the engine.
"""

from __future__ import annotations

from .build_cache import load_build_cache, save_build_cache
from .build_engine import build_engine, check_engine_build
from .build_project import build_project, verify_engine_availability
from .clean_build import clean_project, clean_egg_info
from .cython_compiler import compile_cython_modules, get_cython_module_dirs
from .ninja_compiler import NinjaCompiler
from .build_exe import build_executable, ExecutableBuilder
from .sdl_finder import find_sdl2_dlls
from .build_template import create_spec_file, create_spec_from_template
from .create_hooks import create_runtime_hooks

__all__ = [
    'load_build_cache',
    'save_build_cache',
    'build_engine',
    'check_engine_build',
    'verify_engine_availability',
    'build_project',
    'clean_project',
    'clean_egg_info',
    'compile_cython_modules',
    'get_cython_module_dirs',
    'NinjaCompiler',
    'build_executable',
    'ExecutableBuilder',
    'find_sdl2_dlls',
    'create_spec_file',
    'create_spec_from_template',
    'create_runtime_hooks',
]
