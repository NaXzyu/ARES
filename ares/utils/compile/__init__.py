"""Compilation utilities for the Ares Engine."""

from __future__ import annotations

from ares.utils.const import (
    PYD_EXTENSION,
    SO_EXTENSION,
    C_EXTENSION,
    PYTHON_EXT,
    REQUIRED_PYTHON_VERSION,
    REQUIRED_PYTHON_VERSION_STR,
    ERROR_BUILD_FAILED
)

from .ninja_compiler import NinjaCompiler
from .ext_manager import ExtManager
from .cmodule_manager import CModuleManager
from .cmodule_compiler import CModuleCompiler
from .compile_utils import CompileUtils

__all__ = [
    # Main compilation classes
    "CModuleCompiler",
    "CModuleManager",
    "ExtManager",
    "NinjaCompiler",
    "CompileUtils",
    
    # Constants
    "PYD_EXTENSION",
    "SO_EXTENSION",
    "C_EXTENSION",
    "PYTHON_EXT",
    "REQUIRED_PYTHON_VERSION",
    "REQUIRED_PYTHON_VERSION_STR",
    "ERROR_BUILD_FAILED"
]
