#!/usr/bin/env python3
"""
Custom build_ext command that supports Ninja for faster builds.
"""

import sys
import os
from pathlib import Path
from setuptools.command.build_ext import build_ext

# Get project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class NinjaCompiler(build_ext):
    def finalize_options(self):
        super().finalize_options()
        
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from ares.config import initialize, build_config, config
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
            
            # Load compiler flags from compiler.ini instead of package.ini
            compiler_config = config.load("compiler")
            if compiler_config and compiler_config.has_section("compiler_flags"):
                if os.name == 'nt' and compiler_config.has_option("compiler_flags", "windows"):
                    compiler_flags = compiler_config.get("compiler_flags", "windows")
                    if compiler_flags:
                        self._compiler_flags = compiler_flags.split()
                elif os.name != 'nt' and compiler_config.has_option("compiler_flags", "unix"):
                    compiler_flags = compiler_config.get("compiler_flags", "unix")
                    if compiler_flags:
                        self._compiler_flags = compiler_flags.split()
        except (ImportError, AttributeError):
            self.parallel = False
            
    def build_extensions(self):
        # Apply compiler flags from package.ini if available
        if hasattr(self, '_compiler_flags') and self._compiler_flags:
            for ext in self.extensions:
                if not hasattr(ext, 'extra_compile_args') or ext.extra_compile_args is None:
                    ext.extra_compile_args = []
                ext.extra_compile_args.extend(self._compiler_flags)
                
        super().build_extensions()
