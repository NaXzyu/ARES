"""
Package configuration settings for the Ares Engine project.
"""

from .base_config import BaseConfig

class PackageConfig(BaseConfig):

    def __init__(self):
        super().__init__("package")
    
    def get_package_data(self):
        """Get package data configuration as a dictionary."""
        package_data = {}
        
        if self.config.has_section("package_data"):
            for key, value in self.config.items("package_data"):
                package_data[key] = [line.strip() for line in value.splitlines() if line.strip()]
        
        return package_data
    
    def get_extensions(self):
        """Get extension module definitions."""
        extensions = {}
        
        if self.config.has_section("extensions"):
            for name, path_spec in self.config.items("extensions"):
                extensions[name] = path_spec
        
        return extensions
    
    def add_extension(self, name, module_spec):
        """Add or update an extension definition."""
        self.set("extensions", name, module_spec)
        return True
    
    def remove_extension(self, name):
        """Remove an extension definition."""
        if self.config.has_section("extensions") and self.config.has_option("extensions", name):
            self.config.remove_option("extensions", name)
            return True
        return False
