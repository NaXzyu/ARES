#!/usr/bin/env python3
"""Build script for Ares Engine package and executable."""

import os
import sys
import subprocess
import shutil
import time
import datetime
import argparse
import json
import hashlib
from pathlib import Path

FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parent.parent
BUILD_DIR = PROJECT_ROOT / "build"
LOGS_DIR = PROJECT_ROOT / "logs"
CACHE_DIR = BUILD_DIR / "cache"
BUILD_CACHE_FILE = CACHE_DIR / "build_cache.json"
BUILD_LOG_PATH = LOGS_DIR / "build.log"

sys.path.insert(0, str(PROJECT_ROOT))

# Import logging after path setup
from ares.utils import log
from ares.utils.utils import format_size, format_time
from ares.config.logging_config import initialize_logging

# Initialize logging
initialize_logging(LOGS_DIR)

def compute_file_hash(file_path):
    """Compute the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_build_cache():
    """Load the build cache from the cache file if it exists."""
    if not BUILD_CACHE_FILE.exists():
        return {"files": {}, "last_build": None}
    
    try:
        with open(BUILD_CACHE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log.warn(f"Warning: Failed to load build cache: {e}")
        return {"files": {}, "last_build": None}

def save_build_cache(cache):
    """Save the build cache to the cache file."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
        with open(BUILD_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except IOError as e:
        log.warn(f"Warning: Failed to save build cache: {e}")

def check_file_changes(extensions, force=False):
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
    
    cache["last_build"] = datetime.datetime.now().isoformat()
    save_build_cache(cache)
    
    return changed_extensions

def check_compiled_modules():
    """Check if the Cython modules are compiled and move them if needed."""
    log.info("Checking for compiled modules...")
    
    cython_dirs = [
        (PROJECT_ROOT / "ares" / "core", "core modules"),
        (PROJECT_ROOT / "ares" / "math", "math modules"),
        (PROJECT_ROOT / "ares" / "physics", "physics modules"),
        (PROJECT_ROOT / "ares" / "renderer", "renderer modules")
    ]
    
    modules_found = False
    
    for cython_dir, desc in cython_dirs:
        for ext in ['.pyd', '.so']:
            if list(cython_dir.glob(f"*{ext}")):
                modules_found = True
                log.info(f"Found compiled {desc}")
                break
    
    if not modules_found:
        build_dirs = [d for d in BUILD_DIR.glob("lib.*")]
        if build_dirs:
            for cython_dir, desc in cython_dirs:
                module_name = cython_dir.name
                source_path = build_dirs[0] / "ares" / module_name
                if source_path.exists():
                    for ext in ['.pyd', '.so']:
                        for file in source_path.glob(f"*{ext}"):
                            target = cython_dir / file.name
                            log.info(f"Moving {file} to {target}")
                            shutil.copy2(file, target)
                            modules_found = True
    
    if modules_found:
        log.info("Cython modules compiled successfully.")
    else:
        log.error("Error: Could not find compiled Cython modules.")
        sys.exit(1)
        
    return modules_found

def get_extensions(extra_compile_args=None):
    """Define Cython extension modules for compilation."""
    from setuptools.extension import Extension
    
    if extra_compile_args is None:
        extra_compile_args = []
        
    extensions = []
    
    # Get extensions from package.ini
    sys.path.insert(0, str(PROJECT_ROOT))
    from ares.config import config
    package_config = config.load("package")
    
    if package_config and package_config.has_section("extensions"):
        for name, path_spec in package_config.items("extensions"):
            if ":" not in path_spec:
                log.error(f"Error: Invalid extension format for {name}: {path_spec}")
                log.error("Extension format should be 'module.name:path/to/file.pyx'")
                sys.exit(1)
                
            module_name, pyx_path = path_spec.split(":", 1)
            pyx_path = pyx_path.strip()
            
            if not Path(pyx_path).exists():
                log.error(f"Error: Extension source file not found: {pyx_path}")
                log.error("Please verify the path is correct in package.ini")
                sys.exit(1)
                
            extensions.append(
                Extension(
                    module_name,
                    [pyx_path],
                    extra_compile_args=extra_compile_args
                )
            )
    
    # Report error if no extensions defined
    if not extensions:
        log.error("Error: No Cython extensions defined in package.ini")
        log.error("Please add extension definitions to the [extensions] section")
        log.error("Format: name = module.name:path/to/file.pyx")
        sys.exit(1)
    
    return extensions

def compile_cython_modules(python_exe, force=False):
    """Compile the Cython modules for the project."""
    from setuptools import setup
    from Cython.Build import cythonize
    
    sys.path.insert(0, str(PROJECT_ROOT))
    from ares.config import initialize, build_config
    initialize()
    
    compiler_directives = {
        'language_level': build_config.getint("cython", "language_level", 3),
        'boundscheck': build_config.getboolean("cython", "boundscheck", False),
        'wraparound': build_config.getboolean("cython", "wraparound", False),
        'cdivision': build_config.getboolean("cython", "cdivision", True),
    }
    
    optimization = build_config.get("compiler", "optimization_level", "O2")
    inplace = build_config.getboolean("build", "inplace", True)
    
    old_argv = sys.argv.copy()
    
    if os.name == 'nt':
        if optimization == "O0":
            opt_flag = "/Od"
        elif optimization == "O1":
            opt_flag = "/O1"
        elif optimization == "O3":
            opt_flag = "/Ox"
        else:
            opt_flag = "/O2"
    else:
        opt_flag = f"-{optimization}"
    
    build_args = ['build_ext']
    if inplace:
        build_args.append('--inplace')
    
    all_extensions = get_extensions(extra_compile_args=[opt_flag])
    
    extensions_to_build = check_file_changes(all_extensions, force)
    
    if not extensions_to_build:
        log.info("No Cython files have changed. Skipping compilation.")
        return check_compiled_modules()
    
    log.info(f"Compiling {len(extensions_to_build)}/{len(all_extensions)} Cython modules...")
    
    if not BUILD_DIR.exists():
        os.makedirs(BUILD_DIR, exist_ok=True)
    temp_setup = BUILD_DIR / "temp_setup.py"
    
    try:
        with open(temp_setup, "w") as f:
            f.write("""
from setuptools import setup
from Cython.Build import cythonize
import sys
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
            
            # Log Cython compilation output to build log
            with open(BUILD_LOG_PATH, 'a') as log_file:
                log_file.write("\n--- Cython Compilation Output ---\n")
                for line in process.stdout:
                    log_file.write(line)
                    # Only print summary info to console
                    if "Cythonizing" in line or "warning" in line.lower() or "error" in line.lower():
                        print(line.strip())
            
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
    
    return check_compiled_modules()

def check_wheel_rebuild_needed(extensions_changed, force=False):
    """Check if wheel package needs to be rebuilt."""
    if force:
        log.info("Force rebuild requested. Rebuilding wheel package.")
        return True
        
    if extensions_changed:
        log.info("Cython extensions were rebuilt. Rebuilding wheel package.")
        return True
        
    cache = load_build_cache()
    py_files_changed = False
    
    # Get last build time for proper comparison
    last_build_time = None
    if cache.get("last_build"):
        try:
            last_build_time = datetime.datetime.fromisoformat(cache["last_build"])
        except (ValueError, TypeError):
            last_build_time = None

    # Find all Python files in the project
    py_files = []
    for root, _, files in os.walk(PROJECT_ROOT / "ares"):
        for file in files:
            if file.endswith(".py"):
                py_files.append(Path(root) / file)
                
    # Check if any Python files have changed
    for py_file in py_files:
        if not py_file.exists():
            continue
            
        current_hash = compute_file_hash(py_file)
        cached_hash = cache["files"].get(str(py_file), None)
        
        if cached_hash != current_hash:
            # If we have stat info, verify file was actually modified after last build
            if last_build_time and py_file.stat().st_mtime < last_build_time.timestamp():
                # File is older than last build but hash changed - update cache without rebuild
                cache["files"][str(py_file)] = current_hash
                continue
                
            log.info(f"File {py_file.relative_to(PROJECT_ROOT)} has changed.")
            cache["files"][str(py_file)] = current_hash
            py_files_changed = True
    
    # Check setup.py file
    setup_py = PROJECT_ROOT / "setup.py"
    if setup_py.exists():
        current_hash = compute_file_hash(setup_py)
        cached_hash = cache["files"].get(str(setup_py), None)
        
        if cached_hash != current_hash:
            if last_build_time and setup_py.stat().st_mtime < last_build_time.timestamp():
                cache["files"][str(setup_py)] = current_hash
            else:
                log.info("setup.py has changed. Rebuilding wheel package.")
                cache["files"][str(setup_py)] = current_hash
                py_files_changed = True
    
    # Save the updated cache
    save_build_cache(cache)
    
    return py_files_changed

def build_engine(python_exe, force=False, output_dir=None):
    """Build the Ares Engine package.
    
    Args:
        python_exe: Path to the Python executable to use
        force: Whether to force rebuilding all modules
        output_dir: Optional custom output directory
        
    Returns:
        bool: True if build succeeded, False otherwise
    """
    log.info(f"Using Python: {python_exe}")
    
    build_start = datetime.datetime.now()
    build_start_time = time.time()
    
    # Update the BUILD_DIR to use the specified output directory
    global BUILD_DIR, CACHE_DIR, BUILD_CACHE_FILE, LOGS_DIR, BUILD_LOG_PATH
    if output_dir:
        BUILD_DIR = Path(output_dir)
        CACHE_DIR = BUILD_DIR / "cache"
        BUILD_CACHE_FILE = CACHE_DIR / "build_cache.json"
    
    # Always ensure logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    sys.path.insert(0, str(PROJECT_ROOT))
    from ares.config import initialize, build_config, config
    initialize()
    log.info("Loaded build configuration")
    
    _ = config.load("package")
    log.info("Loaded package configuration")
    
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    with open(BUILD_LOG_PATH, "a") as log_file:
        log_file.write(f"\n\n--- Build started at {build_start.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    
    log.info("Compiling Cython modules...")
    cython_changed = False
    try:
        if not compile_cython_modules(python_exe, force):
            log.error("Error: Failed to compile Cython modules.")
            # Continue anyway - we'll try to build the wheel
        else:
            cache = load_build_cache()
            if cache.get("rebuilt_modules", False):
                cython_changed = True
                cache["rebuilt_modules"] = False
                save_build_cache(cache)
    except Exception as e:
        log.error(f"Exception during Cython compilation: {e}")
        # Continue anyway - we need to build the wheel even if some Cython modules fail
    
    log.info("Compilation complete. Building packages...")
    
    # Check if wheel rebuild is needed based on changes
    rebuild_needed = check_wheel_rebuild_needed(cython_changed, force)
    
    # Even if no changes detected, check if the wheel exists
    wheel_files = list(BUILD_DIR.glob("ares-*.whl"))
    
    if not rebuild_needed and wheel_files:
        log.info("\nNo changes detected and wheel exists. Using existing packages.")
        
        wheel_file = wheel_files[0]
        wheel_size = os.path.getsize(wheel_file)
        
        log.info(f"Using existing wheel package: {wheel_file}")
        log.info(f"Size: {format_size(wheel_size)}")
        
        # Check for source distribution as well
        sdist_files = list(BUILD_DIR.glob("ares-*.tar.gz"))
        if sdist_files:
            sdist_file = sdist_files[0]
            sdist_size = os.path.getsize(sdist_file)
            log.info(f"Using existing source distribution: {sdist_file}")
            log.info(f"Size: {format_size(sdist_size)}")
    else:
        # Need to rebuild - either changes detected, force rebuild, or missing wheel
        if not wheel_files:
            log.info("\nWheel package not found. Building new packages.")
        elif rebuild_needed:
            log.info("\nChanges detected. Rebuilding packages.")
            
        log.info("\nBuilding wheel package...")
        wheel_start_time = time.time()
        wheel_cmd = [str(python_exe), "-m", "pip", "wheel", ".", "-w", str(BUILD_DIR)]
        try:
            # Capture pip wheel output
            process = subprocess.Popen(
                wheel_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            
            # Log pip wheel output
            with open(BUILD_LOG_PATH, 'a') as log_file:
                log_file.write("\n--- Wheel Build Output ---\n")
                for line in process.stdout:
                    log_file.write(line)
                    # Only print summary info to console
                    if "Processing" in line or "Building wheel" in line or "Created wheel" in line:
                        print(line.strip())
        
            # Wait for process to complete
            ret_code = process.wait()
            if ret_code != 0:
                log.error(f"Wheel build failed with return code {ret_code}")
                return False
            
            wheel_files = list(BUILD_DIR.glob("ares-*.whl"))
            if wheel_files:
                wheel_file = wheel_files[0]
                wheel_size = os.path.getsize(wheel_file)
                log.info(f"Created wheel package: {wheel_file}")
                log.info(f"Size: {format_size(wheel_size)}")
            else:
                log.error("Error: Wheel file not found after build.")
                return False
        except subprocess.CalledProcessError as e:
            log.error(f"Error building wheel: {e}")
            return False
        
        log.info("\nBuilding source distribution...")
        sdist_cmd = [str(python_exe), "setup.py", "sdist", "--dist-dir", str(BUILD_DIR)]
        try:
            subprocess.run(sdist_cmd, check=True)
            
            sdist_files = list(BUILD_DIR.glob("ares-*.tar.gz"))
            if sdist_files:
                sdist_file = sdist_files[0]
                sdist_size = os.path.getsize(sdist_file)
                log.info(f"Created source distribution: {sdist_file}")
                log.info(f"Size: {format_size(sdist_size)}")
            else:
                # Don't fail if sdist fails, as long as we have the wheel
                log.warn("Warning: Source distribution not found after build.")
        except subprocess.CalledProcessError as e:
            log.warn(f"Warning: Error building source distribution: {e}")
            # Continue anyway - as long as we have the wheel file
    
    build_end_time = time.time()
    build_duration = build_end_time - build_start_time
    
    # Check one more time to verify success
    wheel_files = list(BUILD_DIR.glob("ares-*.whl"))
    if not wheel_files:
        log.error("Error: Failed to build engine wheel package.")
        return False
    
    with open(BUILD_LOG_PATH, "a") as log_file:
        log_file.write(f"Build completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Build duration: {format_time(build_duration)}\n")
        log_file.write("Build artifacts:\n")
        wheel_files = list(BUILD_DIR.glob("*.whl"))
        sdist_files = list(BUILD_DIR.glob("*.tar.gz"))
        for file in wheel_files + sdist_files:
            log_file.write(f"  - {file.name} ({format_size(os.path.getsize(file))})\n")
    
    log.info("\n" + "="*50)
    log.info(" BUILD SUMMARY ".center(50, "="))
    log.info("="*50)
    log.info(f"Build time:      {format_time(build_duration)}")
    log.info(f"Build log:       {BUILD_LOG_PATH}")
    log.info("Build artifacts:")
    for file in wheel_files + sdist_files:
        log.info(f"  - {file.name} ({format_size(os.path.getsize(file))})")
    log.info("="*50 + "\n")
    
    log.info(f"\nBuild completed successfully. Packages available in: {BUILD_DIR}")
    log.info("\nTo install the engine, run:")
    wheel_file = wheel_files[0].name if wheel_files else "*.whl"
    log.info(f"  pip install {BUILD_DIR / wheel_file}\n")
    
    # Final verification
    wheel_files = list(BUILD_DIR.glob("ares-*.whl"))
    return len(wheel_files) > 0

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Build the Ares Engine.")
    parser.add_argument('--python', required=True,
                        help='Path to the Python executable to use for building')
    parser.add_argument('--force', action='store_true',
                        help='Force rebuilding all Cython modules and packages')
    parser.add_argument('--output-dir', default=BUILD_DIR,
                        help=f'Directory to output build artifacts (default: {BUILD_DIR})')
    return parser.parse_args()

# Re-add command-line functionality
if __name__ == "__main__":
    args = parse_args()
    if build_engine(args.python, args.force, args.output_dir):
        sys.exit(0)
    else:
        sys.exit(1)