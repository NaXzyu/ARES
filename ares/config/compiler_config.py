"""
Compiler configuration settings for the Ares Engine project.
"""

import os
from .base_config import BaseConfig

class CompilerConfig(BaseConfig):

    def __init__(self):
        super().__init__("compiler")
        self._create_default_config()
        
    def _create_default_config(self):
        """Create default compiler configuration."""
        # Compiler section
        self.set("compiler", "optimization_level", "O2")
        self.set("compiler", "debug_symbols", "False")
        self.set("compiler", "additional_flags", "/favor:AMD64 /DWIN64" if os.name == 'nt' else "-march=native")
        self.set("compiler", "parallel_jobs", "8")
        self.set("compiler", "include_dirs", "")
        self.set("compiler", "library_dirs", "")
        self.set("compiler", "use_ninja", "True")
        self.set("compiler", "enable_lto", "True")
        self.set("compiler", "optimize", "3")
        
        # Compiler flags section
        self.set("compiler_flags", "common", "-O2")
        self.set("compiler_flags", "windows", "/O2 /favor:AMD64 /DWIN64")
        self.set("compiler_flags", "unix", "-march=native")
    
    def get_compiler_flags(self):
        """Get compiler flags based on the current platform and settings."""  
        flags = []
        
        opt_level = self.get("compiler", "optimization_level", "O2")
        if os.name == 'nt':
            if opt_level == "O0":
                flags.append("/Od")
            elif opt_level == "O1":
                flags.append("/O1")
            elif opt_level == "O3":
                flags.append("/Ox")
            else:
                flags.append("/O2")
                
            if self.getboolean("compiler", "debug_symbols", False):
                flags.append("/Zi")
        else:
            flags.append(f"-{opt_level}")
            
            if self.getboolean("compiler", "debug_symbols", False):
                flags.append("-g")
        
        additional = self.get("compiler", "additional_flags", "")
        if additional:
            flags.extend(additional.split())
        
        return flags
    
    def use_ninja(self):
        """Check if Ninja build system should be used."""
        return self.getboolean("compiler", "use_ninja", True)
    
    def get_parallel_jobs(self):
        """Get number of parallel compilation jobs."""
        return self.getint("compiler", "parallel_jobs", 8)
    
    def get_optimization_level(self):
        """Get optimization level for compilation."""
        return self.getint("compiler", "optimize", 3)
    
    def is_lto_enabled(self):
        """Check if link-time optimization is enabled."""
        return self.getboolean("compiler", "enable_lto", True)
    
    def get_include_dirs(self):
        """Get additional include directories."""
        dirs = self.get("compiler", "include_dirs", "")
        return [dir.strip() for dir in dirs.split(",")] if dirs else []
    
    def get_library_dirs(self):
        """Get additional library directories."""
        dirs = self.get("compiler", "library_dirs", "")
        return [dir.strip() for dir in dirs.split(",")] if dirs else []

# Create a global instance for easy access
compiler_config = CompilerConfig()
