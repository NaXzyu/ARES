"""Utility to generate temporary setup.py files for Cython compilation."""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from setuptools.extension import Extension

from ares.utils.const import (
    ERROR_BUILD_FAILED,
    PYD_EXTENSION,
    SO_EXTENSION,
)
from ares.utils.log import log
from ares.utils.paths import Paths

def generate_setup_file(extensions: List[Extension], 
                        compiler_directives: Dict[str, Any], 
                        path: Path) -> None:
    """Generate a temporary setup.py file for compiling Cython extensions.
    
    Args:
        extensions: List of Extension objects to compile
        compiler_directives: Dictionary of Cython compiler directives
        path: Path where the setup.py file should be written
        
    Raises:
        IOError: If the file cannot be written
    """
    try:
        with open(path, "w") as f:
            f.write("""
from setuptools import setup
from Cython.Build import cythonize
from setuptools.extension import Extension

ext_modules = []
""")
            
            for i, ext in enumerate(extensions):
                f.write(f"""
ext_{i} = Extension(
    "{ext.name}", 
    {ext.sources},
    extra_compile_args={ext.extra_compile_args if hasattr(ext, 'extra_compile_args') else None}
)
ext_modules.append(ext_{i})
""")
            
            f.write(f"""
setup(
    name="ares_cython_modules",
    ext_modules=cythonize(
        ext_modules,
        compiler_directives={compiler_directives}
    )
)
""")
    except Exception as e:
        log.error(f"Error generating setup file: {e}")
        raise IOError(f"Failed to generate setup file: {e}")

def filter_compiler_flags(compiler_flags: List[str]) -> List[str]:
    """Filter compiler flags to remove problematic ones.

    Args:
        compiler_flags: List of compiler flags to filter

    Returns:
        Filtered compiler flags
    """
    if not compiler_flags:
        return []
    valid_flags = []
    for flag in compiler_flags:
        if flag not in ['common', 'unix', 'windows']:
            valid_flags.append(flag)
    return valid_flags

def run_subprocess(cmd: List[str], build_log_path: Path) -> None:
    """Run a subprocess and log its output.
    
    Args:
        cmd: List of command arguments
        build_log_path: Path to the log file
        
    Raises:
        RuntimeError: If the subprocess fails
    """
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        universal_newlines=True
    )
    log.log_to_file(build_log_path, "Cython Compilation Output", add_timestamp=True)
    for line in process.stdout:
        log.log_to_file(build_log_path, line.rstrip(), add_timestamp=False, add_newlines=False)
        line = line.strip()
        if "[" in line and "Cythonizing" in line:
            log.info(line)
        elif "warning" in line.lower():
            log.warn(line)
        elif "error" in line.lower():
            log.error(line)
    ret_code = process.wait()
    if ret_code != 0:
        log.error(f"Cython compilation failed with return code {ret_code}")
        raise RuntimeError(f"Cython compilation failed (error code: {ERROR_BUILD_FAILED})")

# Additional utility functions with type annotations

def has_compiled_modules(directory: Path) -> bool:
    """Check if directory contains compiled module files.
    
    Args:
        directory: Directory to check
        
    Returns:
        True if compiled modules exist
    """
    directory = Path(directory)
    for ext in [PYD_EXTENSION, SO_EXTENSION]:
        if list(directory.glob(f"*{ext}")):
            return True
            
    # Check for version-tagged extensions
    if list(directory.glob("*.cp*-*.pyd")) or list(directory.glob("*.cpython-*.so")):
        return True
        
    return False

def find_compiled_module_files(directory: Path) -> Set[str]:
    """Find all compiled module files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        Set of module filenames found
    """
    found_files = set()  # Avoid duplicates
    
    # Standard extensions
    for ext in [PYD_EXTENSION, SO_EXTENSION]:
        for file in Path(directory).glob(f"*{ext}"):
            found_files.add(file.name)
            
    # Version-tagged extensions
    for file in Path(directory).glob(f"*.cp*-*{PYD_EXTENSION}"):
        found_files.add(file.name)
    for file in Path(directory).glob(f"*.cpython-*{SO_EXTENSION}"):
        found_files.add(file.name)
        
    return found_files

def search_lib_dirs_in_locations(search_dirs: List[Path]) -> Set[str]:
    """Search for library directories in multiple locations.
    
    Args:
        search_dirs: List of directories to search
        
    Returns:
        Set of library directories found
    """
    lib_dirs = set()  # Use a set to avoid duplicates
    
    # Search each directory for lib subdirectories
    for search_dir in search_dirs:
        found_dirs = Paths.find_lib_paths(search_dir)
        if found_dirs:
            log.info(f"Found {len(found_dirs)} lib dirs in {search_dir}")
            for dir_path in found_dirs:
                lib_dirs.add(str(dir_path))
                
    return lib_dirs

def copy_module_file(source_file: Path, target_dir: Path) -> bool:
    """Copy a single compiled module file to the target directory.
    
    Args:
        source_file: Path to the source module file
        target_dir: Target directory to copy the module to
        
    Returns:
        True if module was copied or already exists
    """
    import shutil
    
    # Create destination directory
    os.makedirs(target_dir, exist_ok=True)
    target = Path(target_dir) / source_file.name
    
    # Check if file already exists with same content
    if target.exists() and target.stat().st_size == source_file.stat().st_size:
        log.info(f"File {target.name} already exists in destination, skipping")
        return True
        
    log.info(f"Copying {source_file} -> {target}")
    try:
        shutil.copy2(source_file, target)
        return True
    except Exception as e:
        log.error(f"Error copying module: {e}")
        raise IOError(f"Failed to copy module file: {e}")

def scan_and_copy_modules(lib_module_dir: Path, cython_dir: Path) -> bool:
    """Scan a module directory for compiled modules and copy them to target directory.
    
    Args:
        lib_module_dir: Source directory containing compiled modules
        cython_dir: Target directory to copy modules to
        
    Returns:
        True if any modules were found and copied
    """
    if not lib_module_dir.exists():
        return False
        
    log.info(f"Scanning {lib_module_dir} for module files")
    
    module_files = find_compiled_module_files(lib_module_dir)
    modules_found = False
    
    if module_files:
        log.info(f"Found {len(module_files)} compiled modules in {lib_module_dir}")
        for module_file_name in module_files:
            module_file = lib_module_dir / module_file_name
            try:
                copy_module_file(module_file, cython_dir)
                modules_found = True
            except IOError as e:
                log.warn(f"Could not copy module {module_file_name}: {e}")
                
    return modules_found

def get_compiler_directives(build_config) -> Dict[str, Any]:
    """Get Cython compiler directives from build configuration.
    
    Args:
        build_config: Build configuration object
        
    Returns:
        Dictionary of compiler directives
    """
    return {
        'language_level': build_config.get_int("language_level", 3, "cython"),
        'boundscheck': build_config.get_bool("boundscheck", False, "cython"),
        'wraparound': build_config.get_bool("wraparound", False, "cython"),
        'cdivision': build_config.get_bool("cdivision", True, "cython"),
    }

def parse_extension_spec(name: str, 
                         path_spec: str, 
                         extra_compile_args: Optional[List[str]] = None) -> Optional[Extension]:
    """Parse an extension specification from package.ini.
    
    Args:
        name: Name of the extension entry
        path_spec: Specification string in format 'module.name:path/to/file.pyx'
        extra_compile_args: Optional extra compiler arguments
        
    Returns:
        The parsed Extension object, or None if invalid
    """
    log.info(f"Extension definition: {name} = {path_spec}")
    
    if ":" not in path_spec:
        log.error(f"Error: Invalid extension format for {name}: {path_spec}")
        log.error("Extension format should be 'module.name:path/to/file.pyx'")
        return None
        
    module_name, pyx_path = path_spec.split(":", 1)
    pyx_path = pyx_path.strip()
    
    # Get absolute path relative to project root
    full_pyx_path = Paths.get_python_module_path(pyx_path)
    
    if not full_pyx_path.exists():
        log.error(f"Error: Extension source file not found: {full_pyx_path}")
        log.error(f"Working directory: {os.getcwd()}")
        log.error(f"Project root: {Paths.PROJECT_ROOT}")
        log.error("Please verify the path is correct in package.ini")
        return None
        
    extension = Extension(
        module_name,
        [str(full_pyx_path)],
        extra_compile_args=extra_compile_args
    )
    log.info(f"Added extension {module_name} from {full_pyx_path}")
    return extension
