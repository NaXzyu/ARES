"""Module for compiling Cython extensions in the Ares Engine project."""

import os
import sys
import subprocess
from pathlib import Path

from ares.utils import log
from ares.utils.build_utils import compute_file_hash
from ares.build.build_cache import load_build_cache, save_build_cache
from ares.config.config_types import ConfigType  # Add this import
from ares.config import CONFIGS  # Add this import

def get_cython_module_dirs(project_root=None):
    """Get Cython module directories from project configuration."""
    # Default project root if not specified
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent.parent
    
    # Ensure project_root is a Path object
    project_root = Path(project_root)
    
    try:
        # Add project root to path to ensure imports work
        sys.path.insert(0, str(project_root))
        
        # Try to use CONFIGS dictionary first
        try:
            from ares.config.config_types import ConfigType
            from ares.config import CONFIGS
            
            if ConfigType.BUILD in CONFIGS and CONFIGS[ConfigType.BUILD] is not None:
                module_dirs_str = CONFIGS[ConfigType.BUILD].get_raw_cython_module_dirs()
                if module_dirs_str:
                    # Continue with parsing module_dirs_str
                    parsed_modules = []
                    for module_pair in module_dirs_str.split(','):
                        module_pair = module_pair.strip()
                        if ':' in module_pair:
                            module_name, description = module_pair.split(':', 1)
                            parsed_modules.append((module_name.strip(), description.strip()))
                    
                    # Convert to full paths
                    cython_dirs = []
                    for module_name, description in parsed_modules:
                        module_path = project_root / "ares" / module_name
                        cython_dirs.append((module_path, description))
                    
                    if cython_dirs:
                        return cython_dirs
        except (ImportError, KeyError, AttributeError) as e:
            log.warn(f"Could not access BuildConfig from CONFIGS: {e}. Trying direct file access.")
        
        # Fallback to direct config file access if CONFIGS approach failed
        ini_path = project_root / "ares" / "ini" / "build.ini"
        if ini_path.exists():
            import configparser
            parser = configparser.ConfigParser()
            parser.read(ini_path)
            
            if 'cython' in parser and 'module_dirs' in parser['cython']:
                module_dirs_str = parser['cython']['module_dirs']
                
                # Parse module dirs
                parsed_modules = []
                for module_pair in module_dirs_str.split(','):
                    module_pair = module_pair.strip()
                    if ':' in module_pair:
                        module_name, description = module_pair.split(':', 1)
                        parsed_modules.append((module_name.strip(), description.strip()))
                
                # Convert to full paths
                cython_dirs = []
                for module_name, description in parsed_modules:
                    module_path = project_root / "ares" / module_name
                    cython_dirs.append((module_path, description))
                
                if cython_dirs:
                    return cython_dirs
        
        # If we get here, we couldn't find valid module dirs
        log.error("Error: No valid Cython module directories defined in build.ini.")
        log.error("Please define module_dirs in the [cython] section.")
        
        # Use these hardcoded defaults instead of exiting
        log.warn("Using default module directories as fallback")
        default_dirs = [
            ("core", "core modules"),
            ("math", "math modules"),
            ("physics", "physics modules"),
            ("renderer", "renderer modules")
        ]
        
        cython_dirs = []
        for module_name, description in default_dirs:
            module_path = project_root / "ares" / module_name
            cython_dirs.append((module_path, description))
        
        return cython_dirs
        
    except Exception as e:
        import traceback
        log.error(f"Error getting Cython module directories: {e}")
        log.error(traceback.format_exc())
        
        # Return sensible defaults instead of crashing
        default_dirs = [
            (project_root / "ares" / "math", "math modules"),
            (project_root / "ares" / "physics", "physics modules")
        ]
        return default_dirs

def compile_cython_modules(python_exe, project_root, build_dir, build_log_path, force=False):
    """Compile the Cython modules for the project.
    
    Args:
        python_exe: Path to Python executable
        project_root: Path to project root
        build_dir: Path to build directory
        build_log_path: Path to build log file
        force: Whether to force rebuilding all modules
        
    Returns:
        bool: True if compilation succeeded, False otherwise
    """
    from Cython.Build import cythonize
    
    sys.path.insert(0, str(project_root))
    from ares.config import initialize, build_config, compiler_config
    initialize()
    
    # Fix: Remove the int() wrapper and use the correct parameter format for get_int/get_bool
    compiler_directives = {
        'language_level': build_config.get_int("language_level", 3, "cython"),
        'boundscheck': build_config.get_bool("boundscheck", False, "cython"),
        'wraparound': build_config.get_bool("wraparound", False, "cython"),
        'cdivision': build_config.get_bool("cdivision", True, "cython"),
    }
    
    inplace = build_config.get_bool("build", "inplace", True)
    
    old_argv = sys.argv.copy()
    
    # Use compiler_config.get_compiler_flags() to get flags in a consistent way
    compiler_flags = compiler_config.get_compiler_flags()
    
    # Fix: Clean up compiler flags before passing them
    if (compiler_flags is None):
        compiler_flags = []
    
    # Filter out flags like 'common' that are causing warnings
    if compiler_flags:
        # Keep only flags that don't cause "unrecognized source file" warnings
        valid_flags = []
        for flag in compiler_flags:
            if flag not in ['common', 'unix', 'windows']:
                valid_flags.append(flag)
        compiler_flags = valid_flags
    
    build_args = ['build_ext']
    if inplace:
        build_args.append('--inplace')
    
    all_extensions = get_extensions(project_root, extra_compile_args=compiler_flags)
    
    # First check if modules already exist - otherwise force compilation
    modules_already_exist = False
    cython_dirs = get_cython_module_dirs(project_root)
    for cython_dir, desc in cython_dirs:
        for ext in ['.pyd', '.so']:
            if list(cython_dir.glob(f"*{ext}")):
                modules_already_exist = True
                log.info(f"Found existing compiled {desc}")
                break
    
    # Force rebuilding if no modules exist
    if not modules_already_exist:
        log.info("No compiled modules found. Forcing compilation.")
        force = True
    
    extensions_to_build = check_file_changes(all_extensions, project_root, build_dir, force)
    
    if not extensions_to_build:
        log.info("No Cython files have changed. Skipping compilation.")
        return check_compiled_modules(project_root, build_dir)
    
    log.info(f"Compiling {len(extensions_to_build)}/{len(all_extensions)} Cython modules...")
    
    if not build_dir.exists():
        os.makedirs(build_dir, exist_ok=True)
    temp_setup = build_dir / "temp_setup.py"
    
    try:
        with open(temp_setup, "w") as f:
            f.write("""
from setuptools import setup
from Cython.Build import cythonize
from setuptools.extension import Extension

ext_modules = []
""")
            for i, ext in enumerate(extensions_to_build):
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
        
        if extensions_to_build:
            run_cmd = [str(python_exe), str(temp_setup)]
            run_cmd.extend(build_args)
            
            # Capture Cython compiler output
            process = subprocess.Popen(
                run_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            
            # Log Cython compilation output to both build log and through our log system
            with open(build_log_path, 'a') as log_file:
                log_file.write("\n--- Cython Compilation Output ---\n")
                for line in process.stdout:
                    log_file.write(line)
                    # Send compilation progress and warnings through our logger
                    line = line.strip()
                    if "[" in line and "Cythonizing" in line:
                        # Extract the progress info: [1/3] Cythonizing path
                        log.info(line)
                    elif "warning" in line.lower():
                        log.warn(line)  # Changed from log.warning to log.warn
                    elif "error" in line.lower():
                        log.error(line)
            
            # Wait for process to complete
            ret_code = process.wait()
            if ret_code != 0:
                log.error(f"Cython compilation failed with return code {ret_code}")
            
            cache = load_build_cache()
            cache["rebuilt_modules"] = True
            save_build_cache(cache)
        
    finally:
        if temp_setup.exists():
            os.unlink(temp_setup)
        sys.argv = old_argv
    
    return check_compiled_modules(project_root, build_dir)

def check_compiled_modules(project_root, build_dir):
    """Check if the Cython modules are compiled and move them if needed."""
    log.info("Checking for compiled modules...")
    
    # Get Cython directories using the centralized function
    cython_dirs = get_cython_module_dirs(project_root)
    
    modules_found = False
    
    # First check directly in the module directories
    for cython_dir, desc in cython_dirs:
        log.info(f"Checking directory: {cython_dir}")
        for ext in ['.pyd', '.so']:
            if list(cython_dir.glob(f"*{ext}")):
                modules_found = True
                log.info(f"Found compiled {desc}")
                break
    
    if not modules_found:
        # Look in the build directory - need to find the specific platform directory
        log.info(f"No modules found directly in module dirs")
        log.info(f"Searching build directory: {build_dir}...")
        
        # Directly look for the standard setuptools build directory pattern
        lib_dirs = set()  # Use a set to avoid duplicates
        
        # DIRECT SEARCH: Look for the specific lib.* directory which is the standard setuptools build output
        direct_lib_dirs = list(build_dir.glob("lib.*"))
        if direct_lib_dirs:
            log.info(f"Found {len(direct_lib_dirs)} build lib directories")
            for dir_path in direct_lib_dirs:
                lib_dirs.add(str(dir_path))  # Convert to string for set deduplication
        
        # PARENT SEARCH: Look in parent directory if we're in an engine subdirectory
        parent_build = build_dir.parent
        parent_lib_dirs = list(parent_build.glob("lib.*"))
        if parent_lib_dirs:
            log.info(f"Found {len(parent_lib_dirs)} lib dirs in parent: {parent_build}")
            for dir_path in parent_lib_dirs:
                lib_dirs.add(str(dir_path))
            
        # PROJECT ROOT SEARCH: Also look in project build directory as a fallback
        project_build = project_root / "build"
        if project_build.exists():
            project_lib_dirs = list(project_build.glob("lib.*"))
            if project_lib_dirs:
                log.info(f"Found {len(project_lib_dirs)} lib dirs in project root build: {project_build}")
                for dir_path in project_lib_dirs:
                    lib_dirs.add(str(dir_path))
        
        # Search in the temp.* directory as well (another setuptools standard)
        temp_dirs = list(build_dir.glob("temp.*"))
        if temp_dirs:
            log.info(f"Found {len(temp_dirs)} temp build directories")
            
        # Convert back to Path objects
        lib_dirs = [Path(d) for d in lib_dirs]
        log.info(f"Found {len(lib_dirs)} unique library directories")
        
        # Check each lib directory for compiled modules
        for lib_dir in lib_dirs:
            ares_dir = lib_dir / "ares"
            if not ares_dir.exists():
                continue
                
            log.info(f"Checking {ares_dir} for compiled modules")
            
            # Check each module type directory
            for cython_dir, desc in cython_dirs:
                module_name = cython_dir.name
                lib_module_dir = ares_dir / module_name
                
                if lib_module_dir.exists():
                    log.info(f"Scanning {lib_module_dir} for module files")
                    
                    # Look for Cython-compiled files with any naming pattern
                    # This handles platform and version specifics like .cp312-win_amd64.pyd
                    module_files = []
                    # Standard extensions
                    for ext in ['.pyd', '.so']:
                        module_files.extend(list(lib_module_dir.glob(f"*{ext}")))
                    # Version-tagged extensions like .cp312-win_amd64.pyd
                    module_files.extend(list(lib_module_dir.glob("*.cp*-*.pyd")))
                    module_files.extend(list(lib_module_dir.glob("*.cpython-*.so")))
                    
                    if module_files:
                        log.info(f"Found {len(module_files)} compiled modules in {lib_module_dir}")
                        for module_file in module_files:
                            # Create destination directory
                            os.makedirs(cython_dir, exist_ok=True)
                            # Copy module to destination
                            target = cython_dir / module_file.name
                            
                            # Check if file already exists and has the same content
                            if target.exists() and target.stat().st_size == module_file.stat().st_size:
                                log.info(f"File {target.name} already exists in destination, skipping")
                                modules_found = True
                                continue
                                
                            log.info(f"Copying {module_file} -> {target}")
                            try:
                                import shutil
                                shutil.copy2(module_file, target)
                                modules_found = True
                            except Exception as e:
                                log.error(f"Error copying module: {e}")
    
    # Final verification - check all module directories again after copying
    modules_found = False
    for cython_dir, desc in cython_dirs:
        found_files = set()  # Use a set to avoid duplicates
        for ext in ['.pyd', '.so']:
            for file in cython_dir.glob(f"*{ext}"):
                found_files.add(file.name)
        # Also look for version-tagged extensions
        for file in cython_dir.glob("*.cp*-*.pyd"):
            found_files.add(file.name)
        for file in cython_dir.glob("*.cpython-*.so"):
            found_files.add(file.name)
        
        if found_files:
            modules_found = True
            log.info(f"Found {len(found_files)} compiled modules in {cython_dir}")
            for file_name in found_files:
                log.info(f"  {file_name}")
    
    if modules_found:
        log.info("Cython modules compiled successfully.")
        return True
    else:
        # Last-ditch effort to find any compiled modules anywhere
        log.error("Could not find compiled Cython modules in standard locations.")
        log.error("Emergency search for .pyd and .so files in build tree...")
        
        # Print the build tree structure to help diagnose
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                if file.endswith('.pyd') or file.endswith('.so') or 'vector' in file or 'matrix' in file or 'collision' in file:
                    log.error(f"Found potential module: {Path(root) / file}")
        
        # Print the build directory structure to get more info
        log.error("\nBuild directory contents:")
        _print_dir_tree(build_dir, max_depth=3)
        
        log.error("Error: Could not find or copy compiled Cython modules.")
        sys.exit(1)
        
    return modules_found

def _print_dir_tree(directory, max_depth=3, current_depth=0):
    """Helper function to print directory structure for debugging."""
    if current_depth > max_depth:
        log.error(f"{' ' * current_depth * 2}...")
        return
    
    try:
        log.error(f"{' ' * current_depth * 2}{directory.name}/")
        if directory.is_dir():
            for item in directory.iterdir():
                if item.is_dir():
                    _print_dir_tree(item, max_depth, current_depth + 1)
                else:
                    log.error(f"{' ' * (current_depth + 1) * 2}{item.name}")
    except Exception as e:
        log.error(f"{' ' * current_depth * 2}Error: {e}")

def get_extensions(project_root, extra_compile_args=None):
    """Define Cython extension modules for compilation."""
    from setuptools.extension import Extension
    import traceback
    
    if extra_compile_args is None:
        extra_compile_args = []
        
    extensions = []
    
    try:
        # Instead of using package_config from ares.config, load the package.ini directly from project
        ini_dir = Path(project_root) / "ares" / "ini"
        package_ini_path = ini_dir / "package.ini"
        
        log.info(f"Extension loading: Looking for package.ini at {package_ini_path}")
        
        if not package_ini_path.exists():
            log.error(f"Extension loading: package.ini not found at {package_ini_path}")
            return []
            
        # Use ConfigParser directly to avoid initialization complexities
        import configparser
        parser = configparser.ConfigParser()
        parser.read(package_ini_path)
        
        log.info(f"Extension loading: Loaded package.ini from {package_ini_path}")
        log.info(f"Extension loading: Available sections: {parser.sections()}")
        
        # Check if extensions section exists and show its contents
        if "extensions" in parser:
            extensions_items = list(parser.items("extensions"))
            log.info(f"Extension loading: Found {len(extensions_items)} items in [extensions] section")
            
            for name, path_spec in extensions_items:
                log.info(f"Extension definition: {name} = {path_spec}")
                
                if ":" not in path_spec:
                    log.error(f"Error: Invalid extension format for {name}: {path_spec}")
                    log.error("Extension format should be 'module.name:path/to/file.pyx'")
                    continue
                    
                module_name, pyx_path = path_spec.split(":", 1)
                pyx_path = pyx_path.strip()
                
                # Convert to absolute path relative to project root
                full_pyx_path = Path(project_root) / pyx_path
                
                if not full_pyx_path.exists():
                    log.error(f"Error: Extension source file not found: {full_pyx_path}")
                    log.error(f"Working directory: {os.getcwd()}")
                    log.error(f"Project root: {project_root}")
                    log.error("Please verify the path is correct in package.ini")
                    continue
                    
                extensions.append(
                    Extension(
                        module_name,
                        [str(full_pyx_path)],
                        extra_compile_args=extra_compile_args
                    )
                )
                log.info(f"Added extension {module_name} from {full_pyx_path}")
        else:
            log.error("Extension loading: No [extensions] section found in package.ini")
            
    except Exception as e:
        log.error(f"Exception while loading extensions: {e}")
        log.error(traceback.format_exc())
    
    # If no extensions were found but we need them for the build, provide useful error
    if not extensions:
        log.error("Error: No valid Cython extensions defined in package.ini")
        log.error("Please add extension definitions to the [extensions] section")
        log.error("Format: name = module.name:path/to/file.pyx")
        
        # Print paths to help diagnose the issue
        log.error(f"Project root: {project_root}")
        log.error(f"Current directory: {os.getcwd()}")
        
        # Instead of exiting, we'll raise an exception
        raise ValueError("No valid Cython extensions found - check logs for details")
    
    return extensions

def check_file_changes(extensions, project_root, build_dir, force=False):
    """Check which files have changed since the last build."""
    if force:
        log.info("Force rebuild requested, rebuilding all Cython modules.")
        return extensions
        
    cache = load_build_cache()
    changed_extensions = []
    
    for ext in extensions:
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
                
            pxd_path = source_path.with_suffix('.pxd')
            if pxd_path.exists():
                current_hash = compute_file_hash(pxd_path)
                cached_hash = cache["files"].get(str(pxd_path), None)
                
                if cached_hash != current_hash:
                    log.info(f"File {pxd_path.name} has changed.")
                    cache["files"][str(pxd_path)] = current_hash
                    for ext_obj in extensions:
                        if str(source_path) in ext_obj.sources:
                            if ext_obj not in changed_extensions:
                                changed_extensions.append(ext_obj)
    
        if ext_changed:
            changed_extensions.append(ext)
    
    import datetime
    cache["last_build"] = datetime.datetime.now().isoformat()
    save_build_cache(cache)
    
    return changed_extensions
