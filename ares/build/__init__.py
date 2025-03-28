"""
Build system for the Ares Engine.

This module provides build tools and utilities for compiling and packaging the engine.
"""

from __future__ import annotations

from .build_cache import load_build_cache, save_build_cache, _preprocess_paths_for_json
from .build_engine import build_engine, check_engine_build
from .project_builder import ProjectBuilder
from .clean_build import clean_project, clean_egg_info
from .cython_compiler import compile_cython_modules, get_cython_module_dirs
from .ninja_compiler import NinjaCompiler
from .executable_builder import ExecutableBuilder
from .sdl_finder import find_sdl2_dlls
from .spec_builder import SpecBuilder

__all__ = [
    'load_build_cache',
    'save_build_cache',
    '_preprocess_paths_for_json',
    'build_engine',
    'check_engine_build',
    'ProjectBuilder',
    'clean_project',
    'clean_egg_info',
    'compile_cython_modules',
    'get_cython_module_dirs',
    'NinjaCompiler',
    'ExecutableBuilder',
    'find_sdl2_dlls',
    'SpecBuilder',
]
