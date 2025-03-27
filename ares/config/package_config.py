"""
Package configuration settings for the Ares Engine project.
"""

from .base_config import BaseConfig

class PackageConfig(BaseConfig):

    def __init__(self):
        super().__init__("package")
        self._create_default_config()

    def _create_default_config(self):
        """Create default package configuration."""
        # Package section
        self.set("package", "include_debug_files", "False")
        self.set("package", "create_installer", "True")
        self.set("package", "compression_level", "9")
        self.set("package", "console", "True")
        self.set("package", "onefile", "True")
        self.set("package", "icon_file", "ares/assets/icons/app.ico")
        self.set("package", "target_platform", "auto")
        self.set("package", "splash_screen", "ares/assets/images/splash.png")
        self.set("package", "add_version_info", "True")
        self.set("package", "version_file", "False")

    def is_console_enabled(self):
        """Check if console mode is enabled for executables."""
        return self.getboolean("package", "console", True)
    
    def is_onefile_enabled(self):
        """Check if onefile mode is enabled for executables."""
        return self.getboolean("package", "onefile", True)
    
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
        return self.set("extensions", name, module_spec)

    def remove_extension(self, name):
        """Remove an extension definition."""
        if self.config.has_section("extensions") and self.config.has_option("extensions", name):
            self.config.remove_option("extensions", name)
            return True
        return False
    
    def get_override_dict(self):
        """Get dictionary of important configuration values."""
        return {
            "console": self.is_console_enabled(),
            "onefile": self.is_onefile_enabled(),
            "include_debug_files": self.getboolean("package", "include_debug_files", False),
            "create_installer": self.getboolean("package", "create_installer", True),
            "compression_level": self.getint("package", "compression_level", 9),
            "target_platform": self.get("package", "target_platform", "auto"),
            "extensions": len(self.get_extensions())
        }
    
    def initialize(self, *args, **kwargs):
        """Initialize this configuration."""
        return True
