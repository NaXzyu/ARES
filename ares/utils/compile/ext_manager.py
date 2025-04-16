"""Module for managing Cython extension definitions and build process."""

from pathlib import Path

from ares.utils import log
from ares.utils.build.build_utils import BuildUtils

class ExtManager:
    """Handles Cython extension definition and build tracking."""
    
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
                
            current_hash = BuildUtils.compute_file_hash(source_path)
            cached_hash = cache["files"].get(str(source_path), None)
            
            if cached_hash != current_hash:
                log.info(f"File {source_path.name} has changed or is new.")
                cache["files"][str(source_path)] = current_hash
                ext_changed = True
                
            # Check for .pxd files
            pxd_path = source_path.with_suffix('.pxd')
            if pxd_path.exists():
                current_hash = BuildUtils.compute_file_hash(pxd_path)
                cached_hash = cache["files"].get(str(pxd_path), None)
                
                if cached_hash != current_hash:
                    log.info(f"File {pxd_path.name} has changed.")
                    cache["files"][str(pxd_path)] = current_hash
                    ext_changed = True
                    
                    # Ensure the extension is added to the list of changed extensions
                    for ext_obj in extensions:
                        if ext_obj not in changed_extensions:
                            changed_extensions.append(ext_obj)
                            
        return ext_changed
    