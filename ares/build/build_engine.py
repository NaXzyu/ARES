#!/usr/bin/env python3
"""Build script for Ares Engine package and executable."""

import argparse
import datetime
import os
import shutil
import subprocess
import sys
import time
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
from ares.utils.build_utils import compute_file_hash
from ares.build.cython_compiler import compile_cython_modules
from ares.build.build_cache import load_build_cache, save_build_cache, set_cache_paths

def check_wheel_rebuild_needed(extensions_changed, force=False):
    """
    Determine if wheel rebuild is needed.

    Args:
        extensions_changed (bool): True if Cython extensions have changed.
        force (bool): True to force a rebuild.

    Returns:
        bool: True if the wheel should be rebuilt.
    """
    if force:
        log.info("Force rebuild requested. Rebuilding wheel package.")
        return True
        
    if extensions_changed:
        log.info("Cython extensions were rebuilt. Rebuilding wheel package.")
        return True
        
    cache = load_build_cache(BUILD_CACHE_FILE)
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
            # Verify file modified after last build
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
                py_files_changed = True
    
    # Save the updated cache
    save_build_cache(cache, BUILD_CACHE_FILE, CACHE_DIR)
    
    return py_files_changed

def build_engine(python_exe, force, output_dir, configs):
    """
    Build the Ares Engine package.

    Args:
        python_exe (str): Python executable path.
        force (bool): Force rebuild of modules.
        output_dir (str): Directory where build artifacts will be placed.
        configs (dict): Configuration objects dictionary from ConfigManager.

    Returns:
        bool: True if build succeeds, False otherwise.
    """
    log.info(f"Using Python: {python_exe}")
    
    build_start = datetime.datetime.now()
    build_start_time = time.time()
    
    # Update the BUILD_DIR to use the specified output directory
    global BUILD_DIR, CACHE_DIR, BUILD_CACHE_FILE, LOGS_DIR, BUILD_LOG_PATH
    BUILD_DIR = Path(output_dir)
    CACHE_DIR, BUILD_CACHE_FILE = set_cache_paths(BUILD_DIR)
    
    # Always ensure logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    sys.path.insert(0, str(PROJECT_ROOT))
    
    # We can use the configs directly without extraction since they're already loaded with overrides
    log.info("Using provided build configuration")
    
    # Use the configs dictionary directly - note that we're using ConfigType enum for access
    from ares.config.config_types import ConfigType
    package_data = configs[ConfigType.PACKAGE].get_package_data()
    log.info(f"Loaded package configuration with {len(package_data)} package data entries")
    package_extensions = configs[ConfigType.PACKAGE].get_extensions()
    log.info(f"Found {len(package_extensions)} extension modules in package config")
    
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    with open(BUILD_LOG_PATH, "a") as log_file:
        log_file.write(f"\n\n--- Build started at {build_start.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    
    log.info("Compiling Cython modules...")
    cython_changed = False
    
    if not compile_cython_modules(python_exe, PROJECT_ROOT, BUILD_DIR, BUILD_LOG_PATH, force):
        log.error("Error: Failed to compile Cython modules.")
        raise RuntimeError("Failed to compile Cython modules. Cannot continue with build.")
    
    cache = load_build_cache(BUILD_CACHE_FILE)
    if cache.get("rebuilt_modules", False):
        cython_changed = True
        cache["rebuilt_modules"] = False
        save_build_cache(cache, BUILD_CACHE_FILE, CACHE_DIR)
    
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
        # Run setup.py with sdist directly, avoiding the problematic option
        sdist_cmd = [
            str(python_exe),
            "setup.py",
            "sdist"  # No additional options
        ]
        
        try:
            # Create a modified environment to control where the sdist file goes
            env = os.environ.copy()
            env["PYTHONPATH"] = str(PROJECT_ROOT)
            
            # Run the command with the modified environment
            process = subprocess.run(
                sdist_cmd,
                check=False,  # Don't throw an exception on non-zero exit
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                env=env
            )
            
            # Check output directories for the tar.gz file
            for search_dir in [BUILD_DIR, PROJECT_ROOT / "dist"]:
                sdist_files = list(search_dir.glob("ares-*.tar.gz"))
                if sdist_files:
                    # Move the file to BUILD_DIR if it's not already there
                    if search_dir != BUILD_DIR:
                        for sdist_file in sdist_files:
                            target_file = BUILD_DIR / sdist_file.name
                            shutil.move(str(sdist_file), str(target_file))
                            sdist_file = target_file
                    
                    # Report the file
                    sdist_size = os.path.getsize(sdist_file)
                    log.info(f"Created source distribution: {sdist_file}")
                    log.info(f"Size: {format_size(sdist_size)}")
                    break
            else:
                # No source distribution found
                log.warn("No source distribution was created, but wheel is available.")
                
            # Clean up any "dist" directory that might have been created
            dist_dir = PROJECT_ROOT / "dist"
            if dist_dir.exists() and dist_dir.is_dir():
                try:
                    shutil.rmtree(dist_dir)
                except Exception as e:
                    log.warn(f"Could not remove temporary dist directory: {e}")
                    
        except Exception as e:
            # Log the error but continue - don't fail the build if wheel was created
            log.warn(f"Error building source distribution: {e}")
            log.warn("Continuing with wheel package only.")
        
    # Calculate build duration regardless of which path was taken
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

def check_engine_build(build_dir=None):
    """Check if the engine has been built properly.
    
    Args:
        build_dir: Optional path to build directory. If None, use default engine build path.
        
    Returns:
        bool: True if the engine is built (wheel files exist), False otherwise
    """
    # Determine directory to check - use provided dir or default to BUILD_DIR/engine
    check_dir = Path(build_dir) if build_dir is not None else BUILD_DIR / "engine"
            
    # Check for wheel files - the primary build artifact
    wheel_files = list(check_dir.glob("ares-*.whl"))
    
    # Consider engine built if wheel files exist
    return len(wheel_files) > 0

if __name__ == "__main__":
    args = parse_args()
    
    # Use the global CONFIGS
    from ares.config import CONFIGS
    
    sys.exit(0 if build_engine(args.python, args.force, args.output_dir, configs=CONFIGS) else 1)