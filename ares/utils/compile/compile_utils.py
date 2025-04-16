"""Utility class providing methods for managing Cython compilation in the Ares Engine."""
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from setuptools.extension import Extension

from ares.utils.const import ERROR_BUILD_FAILED
from ares.utils.const import ERROR_INVALID_CONFIGURATION
from ares.utils.const import ERROR_MISSING_DEPENDENCY
from ares.utils.const import PYD_EXTENSION
from ares.utils.const import SO_EXTENSION
from ares.utils.log import log
from ares.utils.paths import Paths

class CompileUtils:
    """Utility class for managing Cython compilation in Ares Engine."""
    
    @staticmethod
    def generate_setup_file(extensions: List[Extension], 
                            compiler_directives: Dict[str, Any], 
                            path: Path) -> Path:
        """Generate a temporary setup.py file for compiling Cython extensions.
        
        Args:
            extensions: List of Extension objects to compile
            compiler_directives: Dictionary of Cython compiler directives
            path: Directory path where the setup.py file should be written
            
        Returns:
            Path: Path to the generated setup.py file
            
        Raises:
            IOError: If the file cannot be written
        """
        # Ensure path is a directory and create setup.py file path
        dir_path = Path(path)
        setup_path = dir_path / "setup.py"
        
        try:
            with open(setup_path, "w") as f:
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
            return setup_path  # Return the path to the generated file
        except Exception as e:
            log.error(f"Error generating setup file: {e}")
            raise IOError(f"Failed to generate setup file: {e}")

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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
        
        module_files = CompileUtils.find_compiled_module_files(lib_module_dir)
        modules_found = False
        
        if module_files:
            log.info(f"Found {len(module_files)} compiled modules in {lib_module_dir}")
            for module_file_name in module_files:
                module_file = lib_module_dir / module_file_name
                try:
                    CompileUtils.copy_module_file(module_file, cython_dir)
                    modules_found = True
                except IOError as e:
                    log.warn(f"Could not copy module {module_file_name}: {e}")
                    
        return modules_found

    @staticmethod
    def get_compiler_directives(configs) -> Dict[str, Any]:
        """Get Cython compiler directives from configuration.
        
        Args:
            configs: Configuration object or dictionary (required)
            
        Returns:
            dict: Dictionary of compiler directives
        
        Raises:
            ValueError: If configs is None
        """
        # Validate that configs is provided
        if configs is None:
            raise ValueError("Config cannot be None when getting compiler directives")
        
        # Initialize the directives dictionary
        directives = {}
        
        # Handle different config types
        if hasattr(configs, "get_int"):  # It's a BaseConfig object
            try:
                language_level = configs.get_int("language_level", 3)
                boundscheck = configs.get_bool("boundscheck", False)
                wraparound = configs.get_bool("wraparound", False)
                cdivision = configs.get_bool("cdivision", True)
                
                directives["language_level"] = language_level
                directives["boundscheck"] = boundscheck
                directives["wraparound"] = wraparound
                directives["cdivision"] = cdivision
            except Exception as e:
                raise RuntimeError(f"Error getting Cython directives from config object: {e}")
           
        elif isinstance(configs, dict):
            try:
                if "language_level" in configs:
                    directives["language_level"] = int(configs["language_level"])
                if "boundscheck" in configs:
                    directives["boundscheck"] = str(configs["boundscheck"]).lower() in ('true', 'yes', 'y', '1')
                if "wraparound" in configs:
                    directives["wraparound"] = str(configs["wraparound"]).lower() in ('true', 'yes', 'y', '1')
                if "cdivision" in configs:
                    directives["cdivision"] = str(configs["cdivision"]).lower() in ('true', 'yes', 'y', '1')
            except Exception as e:
                log.warn(f"Error getting Cython directives from config dictionary: {e}")
        
        log.info(f"Using Cython compiler directives: {directives}")
        return directives

    @staticmethod
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

    @staticmethod
    def check_modules_in_dirs(cython_dirs: List[Tuple[Path, str]], log_message: bool = True) -> bool:
        """Check if compiled modules exist directly in module directories.
        
        Args:
            cython_dirs: List of tuples containing (path, description)
            log_message: Whether to log messages (default: True)
            
        Returns:
            bool: True if modules were found in any of the directories
        """
        modules_found = False
        
        for cython_dir, desc in cython_dirs:
            if log_message:
                log.info(f"Checking directory: {cython_dir}")
                
            if CompileUtils.has_compiled_modules(cython_dir):
                modules_found = True
                if log_message:
                    log.info(f"Found compiled {desc}")
        
        return modules_found

    @staticmethod
    def get_extensions(extra_compile_args=None):
        """Define Cython extension modules for compilation.
        
        Args:
            extra_compile_args: Optional list of compiler arguments
            
        Returns:
            list: List of Extension objects for compilation
            
        Raises:
            ValueError: If no valid Cython extensions are found
            RuntimeError: If there's an error loading extensions
        """
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
                    extension = CompileUtils.parse_extension_spec(name, path_spec, extra_compile_args)
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
            
            # Log the project root and current directory for debugging
            log.error(f"Project root: {Paths.PROJECT_ROOT}")
            log.error(f"Current directory: {os.getcwd()}")
            
            raise ValueError(f"No valid Cython extensions found (error code: {ERROR_INVALID_CONFIGURATION})")
        
        return extensions

    @staticmethod
    def _check_extension_source_changes(ext, cache, extensions, changed_extensions):
        """Check if source files for an extension have changed.
        
        Args:
            ext: Extension object to check
            cache: Build cache dictionary
            extensions: List of all extensions
            changed_extensions: List to collect extensions that need rebuilding
            
        Returns:
            bool: True if extension has changes and needs rebuilding
        """
        from ares.utils.build.build_utils import BuildUtils
        
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
                    
                    # Check if the extension is already in the changed list
                    for ext_obj in extensions:
                        if ext_obj not in changed_extensions:
                            changed_extensions.append(ext_obj)
                            
        return ext_changed

    @staticmethod
    def check_file_changes(extensions, force=False):
        """Check which files have changed since the last build.
        
        Args:
            extensions: List of Extension objects
            force: Whether to force considering all files as changed
            
        Returns:
            list: List of extensions that need rebuilding
        """
        if force:
            log.info("Force rebuild requested, rebuilding all Cython modules.")
            return extensions
        
        # Get the build cache instance
        from ares.utils.build.build_cache import BuildCache
        build_cache = BuildCache.get_instance()
        cache = build_cache.cache
        changed_extensions = []
        
        for ext in extensions:
            # Check if the extension is already in the changed list
            ext_changed = CompileUtils._check_extension_source_changes(ext, cache, extensions, changed_extensions)
            
            if ext_changed and ext not in changed_extensions:
                changed_extensions.append(ext)
        
        # Save the updated cache
        build_cache.save()
        
        return changed_extensions
    

    @staticmethod
    def check_compiled_modules(build_dir: Path) -> bool:
        """Check if the Cython modules are compiled and move them if needed."""
        log.info("Checking for compiled modules...")
        
        # Import requirements at the beginning of the function
        from ares.utils.compile.cmodule_manager import CModuleManager
        
        # Get Cython directories using the centralized function
        cython_dirs = Paths.get_cython_module_path()
        
        # Use the helper method to check module directories
        modules_found = CompileUtils.check_modules_in_dirs(cython_dirs)
        
        if not modules_found:
            # Look in build directory for platform-specific dirs
            log.info(f"No modules found directly in module dirs")
            log.info(f"Searching build directory: {build_dir}...")
            
            # Find all library directories containing build artifacts
            lib_dirs = CModuleManager.find_lib_directories(build_dir)

            # Copy modules from all found directories
            try:
                modules_found = CModuleManager.copy_compiled_modules(lib_dirs, cython_dirs)
            except Exception as e:
                raise RuntimeError(f"Failed to copy compiled modules: {e}")
        
        # Final verification after copying
        modules_found, found_modules = CModuleManager.verify_compiled_modules(cython_dirs)
        
        # Use the log API to display module information
        log.log_module_files(found_modules)
        
        if not modules_found:
            log.error("Could not find or copy compiled Cython modules")
            log.error("This may indicate a compilation failure or incorrect module paths")
            raise RuntimeError(f"Missing required Cython modules (error code: {ERROR_MISSING_DEPENDENCY})")
                
        log.info("Cython modules compiled successfully.")
        return modules_found