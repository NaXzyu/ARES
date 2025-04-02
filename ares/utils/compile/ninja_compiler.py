#!/usr/bin/env python3
"""Custom build_ext command that supports Ninja for faster builds."""

import sys
from setuptools.command.build_ext import build_ext

from ares.utils.const import ERROR_INVALID_CONFIGURATION
from ares.utils.paths import Paths
from ares.utils.utils import verify_python

class NinjaCompiler(build_ext):
    """Custom build_ext command that verifies Python version and uses Ninja."""
    
    def finalize_options(self):
        """Finalize and validate build options, including Python version check."""
        super().finalize_options()
        
        # Check Python version before proceeding
        verify_python()
        
        # Get compiler flags from compiler_config
        try:
            sys.path.insert(0, str(Paths.PROJECT_ROOT))
            from ares.config import initialize, compiler_config
            initialize()
            
            # Get compiler directives using shared utility function
            self._compiler_flags = compiler_config.get_compiler_flags()
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize NinjaCompiler: {e}. "
                              f"Please ensure Ares Engine is properly installed. "
                              f"(error code: {ERROR_INVALID_CONFIGURATION})") from e
            
    def build_extensions(self):
        """Apply compiler flags to all extensions and build them."""
        if hasattr(self, '_compiler_flags') and self._compiler_flags:
            for ext in self.extensions:
                if not hasattr(ext, 'extra_compile_args') or ext.extra_compile_args is None:
                    ext.extra_compile_args = []
                ext.extra_compile_args.extend(self._compiler_flags)
                
        super().build_extensions()
