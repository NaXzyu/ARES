"""Package configuration for Ares Engine."""

import platform
from pathlib import Path

from .base_config import BaseConfig

class PackageConfig(BaseConfig):
    """Configuration class for package and distribution settings."""
    
    def __init__(self):
        """Initialize the package configuration."""
        super().__init__("package", "package")
        self.set("include_debug_files", "False")
        self.set("create_installer", "True")
        self.set("compression_level", "9")
        self.set("console", "True")
        self.set("onefile", "True")
        self.set("icon_file", "ares/assets/icons/app.ico")
        self.set("target_platform", "auto")
        self.set("splash_screen", "ares/assets/images/splash.png")
        self.set("add_version_info", "True")
        self.set("version_file", "False")
        self.set("extensions", ".py,.pyx,.ini,.txt")

    def is_console_enabled(self):
        """Check if console output is enabled for executables.
        
        Returns:
            bool: True if console output should be enabled
        """
        return self.get_bool("console", True)
        
    def is_onefile_enabled(self):
        """Check if executables should be built as one file.
        
        Returns:
            bool: True if one-file mode should be used
        """
        return self.get_bool("onefile", True)
    
    def get_compression_level(self):
        """Get compression level for package.
        
        Returns:
            int: Compression level (0-9, where 0 is no compression)
        """
        return self.get_int("compression_level", 9)
    
    def should_include_debug_files(self):
        """Check if debug files should be included.
        
        Returns:
            bool: True if debug files should be included
        """
        return self.get_bool("include_debug_files", False)
    
    def should_create_installer(self):
        """Check if an installer should be created.
        
        Returns:
            bool: True if an installer should be created
        """
        return self.get_bool("create_installer", True)
    
    def get_icon_file(self):
        """Get the icon file path for the application.
        
        Returns:
            str: Path to the icon file or None if not set
        """
        return self.get("icon_file")
    
    def get_splash_screen(self):
        """Get the splash screen image path.
        
        Returns:
            str: Path to the splash screen image or None if not set
        """
        return self.get("splash_screen")
        
    def get_extensions(self):
        """Get the list of file extensions to include in package data.
        
        Returns:
            list: List of file extensions
        """
        extensions_str = self.get("extensions", ".py,.pyx,.ini,.txt")
        return [ext.strip() for ext in extensions_str.split(",")]
    
    def get_extension_modules(self):
        """Get extension modules configuration.
        
        Returns:
            dict: Dictionary of extension module configurations
        """
        extensions = {}
        if self.parser.has_section("extensions"):
            for key, value in self.parser.items("extensions"):
                extensions[key] = value
        return extensions
        
    def get_package_data(self):
        """Get package data for setuptools.
        
        Returns:
            dict: Package metadata suitable for setuptools.setup()
        """
        # Ensure configuration is loaded
        if not self.loaded:
            self.load()
            
        package_data = {}
        
        # Check if package_data section exists
        if self.parser.has_section("package_data"):
            # Process all package data entries
            for key, value in self.parser.items("package_data"):
                # Split the value by lines and strip comments
                lines = value.strip().split('\n')
                file_patterns = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(';'):
                        # Split at the first semicolon to remove trailing comments
                        pattern = line.split(';', 1)[0].strip()
                        if pattern:
                            file_patterns.append(pattern)
                
                # Only add entry if there are patterns
                if file_patterns:
                    package_data[key] = file_patterns
        
        # Check for platform-specific overrides
        platform_system = platform.system().lower()
        platform_section = f"package_data.{platform_system}"
        
        if self.parser.has_section(platform_section):
            # Apply platform-specific overrides
            for key, value in self.parser.items(platform_section):
                # Process value the same way as above
                lines = value.strip().split('\n')
                file_patterns = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(';'):
                        pattern = line.split(';', 1)[0].strip()
                        if pattern:
                            file_patterns.append(pattern)
                
                if file_patterns:
                    package_data[key] = file_patterns
                
        return package_data
        
    def get_override_dict(self):
        """Get a dictionary of overridable package configuration.
        
        This is used by build systems to detect config changes.
        
        Returns:
            dict: Dictionary of configuration values that affect builds
        """
        return {
            "console": self.is_console_enabled(),
            "onefile": self.is_onefile_enabled(),
            "compression_level": self.get_compression_level(),
            "include_debug_files": self.should_include_debug_files(),
            "create_installer": self.should_create_installer(),
            "extensions": self.get_extensions()
        }
    
    def initialize(self, *args, **kwargs):
        """Initialize this configuration."""
        return True
