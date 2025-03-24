"""
Build system for Ares Engine.

This package contains tools for building the engine, projects, and executables:
- build_engine: Builds the Ares Engine package
- build_project: Builds projects that use Ares Engine
- build_executable: Creates standalone executables
- clean_project: Cleans up build artifacts
"""

__all__ = [
    'build_engine',
    'build_project',
    'build_executable',
    'clean_project',
    'NinjaCompiler',
    'create_spec_file',
    'create_spec_from_template',
    'create_runtime_hooks',
    'BuildState',
]

# Import key functions to expose at package level
from ares.build.build_engine import build_engine
from ares.build.build_project import build_project
from ares.build.build_exe import build_executable
from ares.build.clean_build import clean_project
from ares.build.ninja_compiler import NinjaCompiler
from ares.build.build_template import create_spec_file, create_spec_from_template
from ares.build.create_hooks import create_runtime_hooks
from ares.build.build_state import BuildState
