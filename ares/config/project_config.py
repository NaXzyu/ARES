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
        self.set("project", "company_name", "Ares Engine")
        self.set("project", "product_name", "Ares")
        self.set("project", "file_description", "Game built with Ares Engine")
        
        # Version section
        self.set("version", "major", "0")
        self.set("version", "minor", "1")
        self.set("version", "patch", "0")
        self.set("version", "release_type", "alpha")
        self.set("version", "build", "auto")

    def get_build_config_file(self):
        """Get the path to the build configuration file."""
        return "build.ini"  # Always use build.ini as the default
    
    def get_company_name(self):
        """Get the company name for the project."""
        return self.get("project", "company_name", "Ares Engine")
        
    def get_product_name(self):
        """Get the product name for the project."""
        return self.get("project", "product_name", "Ares")
        
    def get_file_description(self):
        """Get the file description for the project."""
        return self.get("project", "file_description", "Game built with Ares Engine")
    
    def get_version_string(self):
        """Get full version string."""
        major = self.getint("version", "major", 0)
        minor = self.getint("version", "minor", 1)
        patch = self.getint("version", "patch", 0)
        release = self.get("version", "release_type", "alpha")
        return f"{major}.{minor}.{patch}-{release}"

    def get_override_dict(self):
        """Get dictionary of important configuration values."""
        return {
            "company_name": self.get_company_name(),
            "product_name": self.get_product_name(),
            "file_description": self.get_file_description(),
            "version_string": self.get_version_string()
        }
    
    def initialize(self, *args, **kwargs):
        """Initialize this configuration."""
        return True
