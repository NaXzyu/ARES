"""Module for managing compiled Cython modules."""

from pathlib import Path
from typing import Dict, List, Set, Tuple

from ares.utils import log
from ares.utils.const import ERROR_MISSING_DEPENDENCY
from ares.utils.paths import Paths
from .utils import (
    find_compiled_module_files,
    has_compiled_modules,
    scan_and_copy_modules,
    search_lib_dirs_in_locations,
)

class CModuleManager:
    """Handles compiled module discovery, verification, and copying."""

    
    @classmethod
    def find_lib_directories(cls, build_dir: Path) -> Set[str]:
        """Find library directories containing build artifacts."""
        # Define all directories to search
        search_dirs = [
            build_dir,
            build_dir.parent,
            Paths.get_build_path()
        ]
        
        # Remove duplicates and non-existent directories
        search_dirs = [d for d in search_dirs if d.exists()]
        
        return search_lib_dirs_in_locations(search_dirs)
    
    
    @classmethod
    def _check_lib_dir_for_modules(cls, lib_dir: Path, cython_dirs: List[Tuple[Path, str]]) -> bool:
        """Check a specific library directory for compiled modules and copy them."""
        modules_found = False
        
        ares_dir = Paths.get_ares_path(lib_dir)
        if not ares_dir.exists():
            return False
            
        log.info(f"Checking {ares_dir} for compiled modules")
        
        for cython_dir, _ in cython_dirs:
            lib_module_dir = Paths.get_module_build_path(ares_dir, cython_dir)
            
            try:
                if scan_and_copy_modules(lib_module_dir, cython_dir):
                    modules_found = True
            except IOError as e:
                raise RuntimeError(f"Error copying modules from {lib_module_dir}: {e}")
                
        return modules_found
    

    @classmethod
    def copy_compiled_modules(cls, lib_dirs: Set[str], cython_dirs: List[Tuple[Path, str]]) -> bool:
        """Copy compiled modules from library directories to target directories."""
        modules_found = False
        
        # Convert lib_dirs to Path objects if they're strings
        lib_dirs = [Path(d) for d in lib_dirs]
        log.info(f"Found {len(lib_dirs)} unique library directories")
        
        # Check each lib directory for compiled modules
        for lib_dir in lib_dirs:
            if cls._check_lib_dir_for_modules(lib_dir, cython_dirs):
                modules_found = True
        
        return modules_found
    

    @classmethod
    def check_modules_in_dirs(cls, cython_dirs: List[Tuple[Path, str]], log_message: bool = True) -> bool:
        """Check if compiled modules exist directly in module directories."""
        modules_found = False
        
        for cython_dir, desc in cython_dirs:
            if log_message:
                log.info(f"Checking directory: {cython_dir}")
                
            if has_compiled_modules(cython_dir):
                modules_found = True
                if log_message:
                    log.info(f"Found compiled {desc}")
        
        return modules_found
    

    @classmethod
    def check_compiled_modules(cls, build_dir: Path) -> bool:
        """Check if the Cython modules are compiled and move them if needed."""
        log.info("Checking for compiled modules...")
        
        # Get Cython directories using the centralized function
        cython_dirs = Paths.get_cython_module_path()
        
        # Use the helper method to check module directories
        modules_found = cls.check_modules_in_dirs(cython_dirs)
        
        if not modules_found:
            # Look in build directory for platform-specific dirs
            log.info(f"No modules found directly in module dirs")
            log.info(f"Searching build directory: {build_dir}...")
            
            # Find all library directories containing build artifacts
            lib_dirs = cls.find_lib_directories(build_dir)

            # Copy modules from all found directories
            try:
                modules_found = cls.copy_compiled_modules(lib_dirs, cython_dirs)
            except Exception as e:
                raise RuntimeError(f"Failed to copy compiled modules: {e}")
        
        # Final verification after copying
        modules_found, found_modules = cls.verify_compiled_modules(cython_dirs)
        
        # Use the log API to display module information
        log.log_module_files(found_modules)
        
        if not modules_found:
            log.error("Could not find or copy compiled Cython modules")
            log.error("This may indicate a compilation failure or incorrect module paths")
            raise RuntimeError(f"Missing required Cython modules (error code: {ERROR_MISSING_DEPENDENCY})")
            
        log.info("Cython modules compiled successfully.")
        return modules_found
    

    @classmethod
    def verify_compiled_modules(cls, cython_dirs: List[Tuple[Path, str]]) -> Tuple[bool, Dict[str, Dict]]:
        """Verify all compiled modules exist in the specified directories."""
        modules_found = False
        module_files_by_dir = {}
            
        for cython_dir, desc in cython_dirs:
            found_files = find_compiled_module_files(cython_dir)
                
            if found_files:
                modules_found = True
                module_files_by_dir[str(cython_dir)] = {
                    "description": desc,
                    "files": list(found_files)
                }
                    
        return modules_found, module_files_by_dir