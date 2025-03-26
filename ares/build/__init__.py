"""
Build system for the Ares Engine.

This module provides build tools and utilities for compiling and packaging the engine.
"""

from __future__ import annotations

from .build_cache import load_build_cache, save_build_cache
from .build_engine import build_engine, check_engine_built
from .build_project import build_project
from .clean_build import clean_project
from .cython_compiler import compile_cython_modules
from .ninja_compiler import NinjaCompiler

__all__ = [
    'load_build_cache',
    'save_build_cache',
    'build_engine',
    'check_engine_built',
    'build_project',
    'clean_project',
    'compile_cython_modules',
    'NinjaCompiler',
]
