"""
Project configuration settings for the Ares Engine project.
"""

from .base_config import BaseConfig

class ProjectConfig(BaseConfig):
    
    def __init__(self):
        super().__init__("project")
        self._create_default_config()
    
    def _create_default_config(self):
        """Create default project configuration."""
        # Project section
        self.set("project", "console", "True")
        self.set("project", "onefile", "True")
        self.set("project", "include_debug_symbols", "False")
        self.set("project", "build_config_file", "build.ini")
        self.set("project", "company_name", "Ares Engine")
        self.set("project", "product_name", "Ares")
        self.set("project", "file_description", "Game built with Ares Engine")
        
        # Resources section
        self.set("resources", "include_resources", "True")
        self.set("resources", "resource_dir_name", "resources")
        self.set("resources", "compress_resources", "True")

    def is_console_enabled(self):
        """Check if console mode is enabled for executables."""
        return self.getboolean("project", "console", True)
    
    def is_onefile_enabled(self):
        """Check if onefile mode is enabled for executables."""
        return self.getboolean("project", "onefile", True)
    
    def get_build_config_file(self):
        """Get the path to the build configuration file."""
        return self.get("project", "build_config_file", "build.ini")
    
    def get_company_name(self):
        """Get the company name for the project."""
        return self.get("project", "company_name", "Ares Engine")
        
    def get_product_name(self):
        """Get the product name for the project."""
        return self.get("project", "product_name", "Ares")
        
    def get_file_description(self):
        """Get the file description for the project."""
        return self.get("project", "file_description", "Game built with Ares Engine")
