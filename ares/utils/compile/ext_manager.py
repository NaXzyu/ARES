"""Module for managing Cython extension definitions and build process."""

import os
from pathlib import Path

from ares.utils import log
from ares.utils.const import ERROR_INVALID_CONFIGURATION
from ares.utils.paths import Paths
from ares.utils.utils import compute_file_hash
from ares.utils.build.build_cache import BuildCache
from .utils import parse_extension_spec

class ExtManager:
    """Handles Cython extension definition and build tracking."""
    
    @classmethod
    def get_extensions(cls, extra_compile_args=None):
        """Define Cython extension modules for compilation."""
        if extra_compile_args is None:
            extra_compile_args = []
            
        extensions = []
        
        try:
            # Check if package.ini exists in the project root
            package_ini_path = Paths.get_ini_path("package.ini")
            
            log.info(f"Extension loading: Looking for package.ini at {package_ini_path}")
            
            if not package_ini_path.exists():
                log.error(f"Extension loading: package.ini not found at {package_ini_path}")
                return []
                
            # Read the package.ini file
            import configparser
            parser = configparser.ConfigParser()
            parser.read(package_ini_path)
            
            log.info(f"Extension loading: Loaded package.ini from {package_ini_path}")
            log.info(f"Extension loading: Available sections: {parser.sections()}")
            
            # Check if the [extensions] section exists
            if "extensions" in parser:
                extensions_items = list(parser.items("extensions"))
                log.info(f"Extension loading: Found {len(extensions_items)} items in [extensions] section")
                
                # Parse each extension definition
                for name, path_spec in extensions_items:
                    extension = parse_extension_spec(name, path_spec, extra_compile_args)
                    if extension:
                        extensions.append(extension)
            else:
                log.error("Extension loading: No [extensions] section found in package.ini")
                
        except Exception as e:
            raise RuntimeError(f"Error loading extensions: {e}")
        
        # Check if any extensions were found
        if not extensions:
            log.error("Error: No valid Cython extensions defined in package.ini")
            log.error("Please add extension definitions to the [extensions] section")
            log.error("Format: name = module.name:path/to/file.pyx")
            
            ## Log the project root and current directory for debugging
            log.error(f"Project root: {Paths.PROJECT_ROOT}")
            log.error(f"Current directory: {os.getcwd()}")
            
            raise ValueError(f"No valid Cython extensions found (error code: {ERROR_INVALID_CONFIGURATION})")
        
        return extensions
    
    @classmethod
    def _check_extension_source_changes(cls, ext, cache, extensions, changed_extensions):
        """Check if source files for an extension have changed.
        
        Args:
            ext: Extension object to check
            cache: Build cache dictionary
            extensions: List of all extensions
            changed_extensions: List to collect extensions that need rebuilding
            
        Returns:
            bool: True if extension has changes and needs rebuilding
        """
        ext_changed = False
        for source in ext.sources:
            source_path = Path(source)
            if not source_path.exists():
                log.warn(f"Warning: Source file {source} not found.")
                ext_changed = True
                continue
                
            current_hash = compute_file_hash(source_path)
            cached_hash = cache["files"].get(str(source_path), None)
            
            if cached_hash != current_hash:
                log.info(f"File {source_path.name} has changed or is new.")
                cache["files"][str(source_path)] = current_hash
                ext_changed = True
                
            # Check for .pxd files
            pxd_path = source_path.with_suffix('.pxd')
            if pxd_path.exists():
                current_hash = compute_file_hash(pxd_path)
                cached_hash = cache["files"].get(str(pxd_path), None)
                
                if cached_hash != current_hash:
                    log.info(f"File {pxd_path.name} has changed.")
                    cache["files"][str(pxd_path)] = current_hash
                    ext_changed = True
                    
                    # Check if the extension is already in the changed list
                    for ext_obj in extensions:
                        if ext_obj not in changed_extensions:
                            changed_extensions.append(ext_obj)
                            
        return ext_changed
    
    @classmethod
    def check_file_changes(cls, extensions, force=False):
        """Check which files have changed since the last build."""
        if force:
            log.info("Force rebuild requested, rebuilding all Cython modules.")
            return extensions
        
        # Get the build cache instance
        build_cache = BuildCache.get_instance()
        cache = build_cache.cache
        changed_extensions = []
        
        for ext in extensions:
            # Check if the extension is already in the changed list
            ext_changed = cls._check_extension_source_changes(ext, cache, extensions, changed_extensions)
            
            if ext_changed and ext not in changed_extensions:
                changed_extensions.append(ext)
        
        # Save the updated cache
        build_cache.save()
        
        return changed_extensions