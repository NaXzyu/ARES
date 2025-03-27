"""
Build configuration settings for the Ares Engine project.
"""

from .base_config import BaseConfig

class BuildConfig(BaseConfig):

    def __init__(self):
        super().__init__("build")
        self._create_default_config()
        
    def _create_default_config(self):
        # Build section
        self.set("build", "parallel", "True")
        self.set("build", "inplace", "True")
        
        # Resources section
        self.set("resources", "include_resources", "True")
        self.set("resources", "resource_dir_name", "resources")
        self.set("resources", "compress_resources", "True")
        
        # Cython section
        self.set("cython", "module_dirs", "core:core modules, math:math modules, physics:physics modules, renderer:renderer modules")
        self.set("cython", "language_level", "3")
        self.set("cython", "boundscheck", "False")
        self.set("cython", "wraparound", "False")
        self.set("cython", "cdivision", "True")
    
    def get_resource_dir_name(self):
        """Get the name of the resources directory."""
        return self.get("resources", "resource_dir_name", "resources")
    
    def should_include_resources(self):
        """Check if resources should be included in builds."""
        return self.getboolean("resources", "include_resources", True)
    
    def should_compress_resources(self):
        """Check if resources should be compressed."""
        return self.getboolean("resources", "compress_resources", True)
    
    def get_raw_cython_module_dirs(self):
        """Get the raw Cython module directories string from config."""
        return self.get("cython", "module_dirs", "")

    def get_override_dict(self):
        """Get dictionary of important configuration values."""
        # Import here to avoid circular imports
        from ares.build.cython_compiler import get_cython_module_dirs
        
        return {
            "parallel": self.getboolean("build", "parallel", True),
            "inplace": self.getboolean("build", "inplace", True),
            "include_resources": self.should_include_resources(),
            "resource_dir_name": self.get_resource_dir_name(),
            "compress_resources": self.should_compress_resources(),
            "cython_module_dirs": get_cython_module_dirs()
        }
    
    def initialize(self, *args, **kwargs):
        """Initialize this configuration."""
        return True
