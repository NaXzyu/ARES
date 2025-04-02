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
from .utils import (
    generate_setup_file,
    filter_compiler_flags,
    run_subprocess,
    has_compiled_modules,
    find_compiled_module_files,
    search_lib_dirs_in_locations,
    copy_module_file,
    scan_and_copy_modules,
    get_compiler_directives,
    parse_extension_spec
)

__all__ = [
    # Main compilation classes
    "CModuleCompiler",
    "CModuleManager",
    "ExtManager",
    "NinjaCompiler",
    
    # Utility functions
    "copy_module_file",
    "find_compiled_module_files",
    "filter_compiler_flags",
    "generate_setup_file",
    "get_compiler_directives",
    "has_compiled_modules",
    "parse_extension_spec",
    "run_subprocess",
    "scan_and_copy_modules",
    "search_lib_dirs_in_locations",
    
    # Constants
    "PYD_EXTENSION",
    "SO_EXTENSION",
    "C_EXTENSION",
    "PYTHON_EXT",
    "REQUIRED_PYTHON_VERSION",
    "REQUIRED_PYTHON_VERSION_STR",
    "ERROR_BUILD_FAILED"
]
