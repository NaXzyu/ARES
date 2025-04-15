"""
Cython Module Manager for Ares Engine.

This module provides functionality to manage the compilation, verification,
and organization of Cython extension modules used within the Ares Engine.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ares.utils import log
from ares.utils.paths import Paths
from .compile_utils import CompileUtils

class CModuleManager:
    """Manages Cython extension modules for Ares Engine."""
    
    def __init__(self, output_dir: Path, py_exe: Optional[str] = None, configs=None):
        """Initialize the module manager.
        
        Args:
            output_dir: Directory to output compiled modules
            py_exe: Python executable to use
            configs: Configuration dictionary
        """
        self.output_dir = Path(output_dir)
        self.py_exe = py_exe or sys.executable
        self.configs = configs
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
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
        
        return CompileUtils.search_lib_dirs_in_locations(search_dirs)
    
    
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
                if CompileUtils.scan_and_copy_modules(lib_module_dir, cython_dir):
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
    def verify_compiled_modules(cls, cython_dirs: List[Tuple[Path, str]]) -> Tuple[bool, Dict[str, Dict]]:
        """Verify all compiled modules exist in the specified directories."""
        modules_found = False
        module_files_by_dir = {}
            
        for cython_dir, desc in cython_dirs:
            found_files = CompileUtils.find_compiled_module_files(cython_dir)
                
            if found_files:
                modules_found = True
                module_files_by_dir[str(cython_dir)] = {
                    "description": desc,
                    "files": list(found_files)
                }
                    
        return modules_found, module_files_by_dir