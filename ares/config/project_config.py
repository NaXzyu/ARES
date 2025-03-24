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
        self.set("project", "build_config_file", "build.ini")  # Add default build config file reference
        
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
    
    # Methods to get package information now need to reference build_config instead
    # These methods remain for backwards compatibility but delegate to build_config
    def get_company_name(self):
        """Get the company name for the project (now references build config)."""
        # First check if we have local override
        if self.has_option("package", "company_name"):
            return self.get("package", "company_name", "Ares Engine Team")
        
        # Otherwise access from build_config
        from .build_config import build_config
        return build_config.get_company_name()
        
    def get_product_name(self):
        """Get the product name for the project (now references build config)."""
        # First check if we have local override
        if self.has_option("package", "product_name"):
            return self.get("package", "product_name", "Ares Engine")
            
        # Otherwise access from build_config
        from .build_config import build_config
        return build_config.get_product_name()
