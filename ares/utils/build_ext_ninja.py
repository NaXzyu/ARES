#!/usr/bin/env python3
"""
Custom build_ext command that supports Ninja for faster builds.
"""

import sys
from pathlib import Path
from setuptools.command.build_ext import build_ext

# Get project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class BuildExtWithNinja(build_ext):
    def finalize_options(self):
        super().finalize_options()
        
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from ares.config import initialize, build_config
            initialize()
            
            if build_config.getboolean("compiler", "use_ninja", True):
                try:
                    import ninja
                    self.parallel = True
                except ImportError:
                    self.parallel = build_config.getint("compiler", "parallel_jobs", 4) > 1
            else:
                self.parallel = build_config.getint("compiler", "parallel_jobs", 4) > 1
        except (ImportError, AttributeError):
            self.parallel = False
