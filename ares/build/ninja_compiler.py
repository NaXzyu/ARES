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
        
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from ares.config import initialize, build_config, compiler_config
            initialize()
            
            # Check if we should use Ninja
            if build_config.getboolean("compiler", "use_ninja", True):
                try:
                    import ninja
                    self.parallel = True
                except ImportError:
                    self.parallel = build_config.getint("compiler", "parallel_jobs", 4) > 1
            else:
                self.parallel = build_config.getint("compiler", "parallel_jobs", 4) > 1
            
            # Use compiler_config.get_compiler_flags() to get flags in a consistent way
            self._compiler_flags = compiler_config.get_compiler_flags()
            
        except (ImportError, AttributeError):
            self.parallel = False
            
    def build_extensions(self):
        # Apply compiler flags if available
        if hasattr(self, '_compiler_flags') and self._compiler_flags:
            for ext in self.extensions:
                if not hasattr(ext, 'extra_compile_args') or ext.extra_compile_args is None:
                    ext.extra_compile_args = []
                ext.extra_compile_args.extend(self._compiler_flags)
                
        super().build_extensions()
