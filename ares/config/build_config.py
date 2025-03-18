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
        self.set("compiler", "optimization_level", "O2")
        self.set("compiler", "debug_symbols", "False")
        self.set("compiler", "additional_flags", "/favor:AMD64 /DWIN64" if os.name == 'nt' else "-march=native")
        self.set("compiler", "parallel_jobs", "4")
        self.set("compiler", "include_dirs", "")
        self.set("compiler", "library_dirs", "")
        self.set("compiler", "use_ninja", "True")
        self.set("compiler", "enable_lto", "True")

        self.set("packager", "include_debug_files", "False")
        self.set("packager", "create_installer", "True")
        self.set("packager", "compression_level", "9")
        self.set("packager", "onefile", "True")
        self.set("packager", "icon_file", "ares/assets/icons/app.ico")
        self.set("packager", "target_platform", "auto")
        self.set("packager", "splash_screen", "ares/assets/images/splash.png")
        self.set("packager", "add_version_info", "True")
        self.set("packager", "company_name", "Ares Engine Team")
        self.set("packager", "product_name", "Ares Engine")
        self.set("packager", "file_description", "Cross-platform game engine with Cython acceleration")
        
        self.set("assets", "compress_textures", "True")
        self.set("assets", "audio_quality", "medium")
        self.set("assets", "bundle_assets", "True")
        self.set("assets", "exclude_patterns", "*.psd, *.xcf, *.blend, *.max, *.mb, *.ma, *.fbx")
        self.set("assets", "include_source_maps", "False")
        self.set("assets", "convert_models", "True")
        self.set("assets", "optimize_assets", "True")
        self.set("assets", "asset_compression", "zlib")
        
        self.set("version", "major", "0")
        self.set("version", "minor", "1")
        self.set("version", "patch", "0")
        self.set("version", "release_type", "alpha")
        self.set("version", "build", "auto")
        
        self.set("build", "pkg_cfg", "pkg_data")
    
    def get_compiler_flags(self):  
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
        return self.get("build", "pkg_cfg", "pkg_data")
