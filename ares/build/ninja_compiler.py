#!/usr/bin/env python3
"""
Custom build_ext command that supports Ninja for faster builds.
"""

import sys
from pathlib import Path
from setuptools.command.build_ext import build_ext

# Get project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class NinjaCompiler(build_ext):
    def finalize_options(self):
        super().finalize_options()
        
        # Get compiler flags from compiler_config
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from ares.config import initialize, compiler_config
            initialize()
            
            # Use compiler_config flags directly
            self._compiler_flags = compiler_config.get_compiler_flags()
            
        except Exception as e:
            # Raise any error that occurs to exit the program gracefully
            raise RuntimeError(f"Failed to initialize NinjaCompiler: {e}. Please ensure Ares Engine is properly installed.") from e
            
    def build_extensions(self):
        # Apply compiler flags if available
        if hasattr(self, '_compiler_flags') and self._compiler_flags:
            for ext in self.extensions:
                if not hasattr(ext, 'extra_compile_args') or ext.extra_compile_args is None:
                    ext.extra_compile_args = []
                ext.extra_compile_args.extend(self._compiler_flags)
                
        super().build_extensions()
