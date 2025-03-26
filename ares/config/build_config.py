"""
Build configuration settings for the Ares Engine project.
"""

import os
from .base_config import BaseConfig

class BuildConfig(BaseConfig):

    def __init__(self):
        super().__init__("build")
        self._create_default_config()
        
    def _create_default_config(self):
        # Package section
        self.set("package", "include_debug_files", "False")
        self.set("package", "create_installer", "True")
        self.set("package", "compression_level", "9")
        self.set("package", "onefile", "True")
        self.set("package", "icon_file", "ares/assets/icons/app.ico")
        self.set("package", "target_platform", "auto")
        self.set("package", "splash_screen", "ares/assets/images/splash.png")
        self.set("package", "add_version_info", "True")
        self.set("package", "company_name", "Ares Engine")
        self.set("package", "product_name", "Ares")
        self.set("package", "file_description", "Game built with Ares Engine")
        self.set("package", "version_file", "False")
        
        # Assets section
        self.set("assets", "compress_textures", "True")
        self.set("assets", "audio_quality", "medium")
        self.set("assets", "bundle_assets", "True")
        self.set("assets", "exclude_patterns", "*.psd, *.xcf, *.blend, *.max, *.mb, *.ma, *.fbx")
        self.set("assets", "include_source_maps", "False")
        self.set("assets", "convert_models", "True")
        self.set("assets", "optimize_assets", "True")
        self.set("assets", "asset_compression", "zlib")
        
        # Version section
        self.set("version", "major", "0")
        self.set("version", "minor", "1")
        self.set("version", "patch", "0")
        self.set("version", "release_type", "alpha")
        self.set("version", "build", "auto")
        
        # Build section
        self.set("build", "parallel", "True")
        self.set("build", "inplace", "True")
        self.set("build", "package_config", "package")
        
        # Cython section
        self.set("cython", "language_level", "3")
        self.set("cython", "boundscheck", "False")
        self.set("cython", "wraparound", "False")
        self.set("cython", "cdivision", "True")
    
    def get_version_string(self):
        major = self.getint("version", "major", 0)
        minor = self.getint("version", "minor", 1)
        patch = self.getint("version", "patch", 0)
        release = self.get("version", "release_type", "alpha")
        
        return f"{major}.{minor}.{patch}-{release}"
    
    def increment_patch_version(self):
        current = self.getint("version", "patch", 0)
        self.set("version", "patch", str(current + 1))
    
    def get_package_data_config(self):
        return self.get("build", "package_config", "package")
    
    # Helper methods for package properties
    def get_company_name(self):
        """Get the company name for the project."""
        return self.get("package", "company_name", "Ares Engine")
    
    def get_product_name(self):
        """Get the product name for the project."""
        return self.get("package", "product_name", "Ares")
        
    def get_file_description(self):
        """Get the file description for the project."""
        return self.get("package", "file_description", "Game built with Ares Engine")
