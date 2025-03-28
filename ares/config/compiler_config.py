"""
Compiler configuration settings for the Ares Engine project.
"""

from .base_config import BaseConfig
from ares.utils.utils import is_windows

class CompilerConfig(BaseConfig):

    def __init__(self):
        super().__init__("compiler")
        self._create_default_config()
        
    def _create_default_config(self):
        """Create default compiler configuration."""
        # Compiler section
        self.set("compiler", "optimization_level", "O3")
        self.set("compiler", "debug_symbols", "False")
        self.set("compiler", "additional_flags", "/favor:AMD64 /DWIN64" if is_windows() else "-march=native")
        self.set("compiler", "parallel_jobs", "8")
        self.set("compiler", "include_dirs", "")
        self.set("compiler", "library_dirs", "")
        self.set("compiler", "use_ninja", "True")
        self.set("compiler", "enable_lto", "True")
        self.set("compiler", "optimize", "3")
        
        # Compiler flags section
        self.set("compiler_flags", "common", "")
        self.set("compiler_flags", "windows", "/O2 /GL /favor:AMD64 /DWIN64 /EHsc /MP /fp:fast")
        self.set("compiler_flags", "unix", "-O3 -march=native -mtune=native -ffast-math -Wall")
    
    def get_compiler_flags(self):
        """Get compiler flags based on the current platform and settings."""  
        flags = []
        
        # Skip common flags and only use platform-specific flags
        if is_windows():
            platform_flags = self.get("compiler_flags", "windows", "")
            if platform_flags:
                flags.extend(platform_flags.split())
        else:
            # For Unix-like systems, we can use both common and unix flags
            common_flags = self.get("compiler_flags", "common", "")
            if common_flags:
                flags.extend(common_flags.split())
                
            platform_flags = self.get("compiler_flags", "unix", "")
            if platform_flags:
                flags.extend(platform_flags.split())
        
        # Add any debug symbols if needed
        if self.get_bool("compiler", "debug_symbols", False):
            if is_windows():
                flags.append("/Zi")
            else:
                flags.append("-g")
        
        return flags
    
    def use_ninja(self):
        """Check if Ninja build system should be used.""" 
        return self.get_bool("compiler", "use_ninja", True)
    
    def get_parallel_jobs(self):
        """Get number of parallel compilation jobs.""" 
        return self.get_int("compiler", "parallel_jobs", 8)
    
    def get_optimization_level(self):
        """Get optimization level for compilation.""" 
        return self.get_int("compiler", "optimize", 3)
    
    def is_lto_enabled(self):
        """Check if link-time optimization is enabled.""" 
        return self.get_bool("compiler", "enable_lto", True)
    
    def get_include_dirs(self):
        """Get additional include directories.""" 
        dirs = self.get("compiler", "include_dirs", "")
        return [dir.strip() for dir in dirs.split(",")] if dirs else []
    
    def get_library_dirs(self):
        """Get additional library directories.""" 
        dirs = self.get("compiler", "library_dirs", "")
        return [dir.strip() for dir in dirs.split(",")] if dirs else []
    
    def get_override_dict(self):
        """Get dictionary of important configuration values."""
        return {
            "optimization_level": self.get("compiler", "optimization_level", "O3"),
            "debug_symbols": self.get_bool("compiler", "debug_symbols", False),
            "use_ninja": self.use_ninja(),
            "parallel_jobs": self.get_parallel_jobs(),
            "enable_lto": self.is_lto_enabled(),
            "include_dirs": self.get_include_dirs(),
            "library_dirs": self.get_library_dirs(),
            "platform_flags": "windows" if is_windows() else "unix"
        }
    
    def initialize(self, *args, **kwargs):
        """Initialize this configuration."""
        return True
