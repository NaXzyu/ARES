#!/usr/bin/env python3
"""Build script for Ares Engine package and executable."""

import datetime
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from ares.config.config_types import ConfigType
from ares.utils import log
from ares.utils.build.build_cache import BuildCache
from ares.utils.build.build_telemetry import BuildTelemetry
from ares.utils.build.utils import compute_file_hash
from ares.utils.compile import CModuleCompiler
from ares.utils.paths import Paths
from ares.utils.const import (
    PYTHON_EXT,
    SETUP_FILE_NAME,
    ENGINE_BUILD_SOURCE_COMMAND,
    ENGINE_BUILDER_WHEEL_COMMAND,
    BUILD_LOG_WHEEL_HEADER,
)

# Set up the environment for the script
sys.path.insert(0, str(Paths.PROJECT_ROOT))


class EngineBuilder:
    """Builds the Ares Engine package and executable."""
    
    def __init__(self, python_exe, output_dir, force=False, configs=None):
        """Initialize the engine builder.
        
        Args:
            python_exe (str): Path to Python executable to use for building
            output_dir (str or Path): Directory to output build artifacts
            force (bool): Force rebuilding all modules and packages
            configs (dict): Configuration objects dictionary from ConfigManager
        """
        self.python_exe = python_exe
        self.output_dir = Path(output_dir)
        self.force = force
        self.configs = configs
        
        # Set up build state
        self.build_start_time = None
        self.build_duration = None
        self.output_path = None
        self.cache_path = None
        self.build_cache_file = None
        self.has_changed = False
        self.cache = BuildCache()
        
    def check_for_rebuild(self, extensions_changed):
        """
        Determine if wheel rebuild is needed.
    
        Args:
            extensions_changed (bool): True if Cython extensions have changed.
    
        Returns:
            bool: True if the wheel should be rebuilt.
        """
        if self.force:
            log.info("Force rebuild requested. Rebuilding wheel package.")
            return True
            
        if extensions_changed:
            log.info("Cython extensions were rebuilt. Rebuilding wheel package.")
            return True
            
        # Check if the cache file exists
        cache_data = self.cache.load()
        py_files_changed = False
        
        # Check if the cache file is empty
        last_build_time = None
        if cache_data.get("last_build"):
            try:
                last_build_time = datetime.datetime.fromisoformat(cache_data["last_build"])
            except (ValueError, TypeError):
                last_build_time = None
    
        # Get all Python files in the Ares directory
        py_files = []
        ares_path = Paths.get_module_path("") # Get the main ares path
        for root, _, files in os.walk(ares_path):
            for file in files:
                if file.endswith(PYTHON_EXT):
                    py_files.append(Path(root) / file)
                    
        # Check for changes in Python files
        for py_file in py_files:
            if not py_file.exists():
                continue
                
            current_hash = compute_file_hash(py_file)
            cached_hash = cache_data["files"].get(str(py_file), None)
            
            if cached_hash != current_hash:
                # Check if the file was modified before the last build time
                if last_build_time and py_file.stat().st_mtime < last_build_time.timestamp():
                    # If file was modified before last build, update cache without rebuilding
                    cache_data["files"][str(py_file)] = current_hash
                    continue
                    
                log.info(f"File {py_file.relative_to(Paths.PROJECT_ROOT)} has changed.")
                cache_data["files"][str(py_file)] = current_hash
                py_files_changed = True
        
        # Check setup.py file for changes
        setup_py = Paths.get_python_module_path(SETUP_FILE_NAME)
        if setup_py.exists():
            current_hash = compute_file_hash(setup_py)
            cached_hash = cache_data["files"].get(str(setup_py), None)
            
            if cached_hash != current_hash:
                if last_build_time and setup_py.stat().st_mtime < last_build_time.timestamp():
                    cache_data["files"][str(setup_py)] = current_hash
                else:
                    log.info(f"{SETUP_FILE_NAME} has changed. Rebuilding wheel package.")
                    py_files_changed = True
        
        # Update last build time in cache
        self.cache.cache.update(cache_data)
        self.cache.save()
        
        return py_files_changed

    def verify_wheel(self):
        """
        Verify that wheel package was successfully built in the output directory.
            
        Raises:
            RuntimeError: If wheel files don't exist
        """
        wheel_files = Paths.find_wheel_files(self.output_path)
        if not wheel_files:
            raise RuntimeError("Failed to build engine wheel package.")

    def _compile_cmodules(self):
        """
        Compile Cython extension modules.
        
        Raises:
            RuntimeError: If compilation fails
        """
        log.info("Compiling Cython modules...")
        
        # Use CModuleCompiler directly
        if not CModuleCompiler.compile(self.python_exe, self.output_path, Paths.get_build_log_file(), self.force):
            raise RuntimeError("Failed to compile Cython modules. Cannot continue with build.")
        
        # Check if the cache file exists
        self.has_changed = self.cache.check_and_reset_rebuild_status()
        
        log.info("Compilation complete.")
    
    def _build_wheel(self):
        """
        Build wheel package for the engine.
        
        Raises:
            RuntimeError: If wheel build fails
        """
        log.info("Building wheel package...")
        wheel_cmd = [
            str(self.python_exe), 
            "-m", 
            "pip"
        ] + ENGINE_BUILDER_WHEEL_COMMAND + [str(self.output_path)]
        
        try:
            # Capture pip wheel output
            process = subprocess.Popen(
                wheel_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            
            # Log the output to a file
            success = log.log_process_output(
                process,
                Paths.get_build_log_file(),
                header=BUILD_LOG_WHEEL_HEADER
            )
            
            if not success:
                raise RuntimeError("Wheel build failed with non-zero return code")
            
            wheel_files = Paths.find_wheel_files(self.output_path)
            if wheel_files:
                wheel_file = wheel_files[0]
                log.info(f"Created wheel package: {wheel_file}")
                log.info(f"Size: {Paths.get_formatted_file_size(wheel_file)}")
            else:
                raise RuntimeError("Wheel file not found after build.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error building wheel: {e}")

    def _build_sdist(self):
        """
        Build source distribution package for the engine.
        
        Raises:
            RuntimeError: If build fails and no wheels exist
        """
        log.info("Building source distribution...")
        # Check if the output directory exists
        sdist_cmd = [
            str(self.python_exe),
            SETUP_FILE_NAME
        ] + ENGINE_BUILD_SOURCE_COMMAND
        
        # Set up environment variables
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Paths.PROJECT_ROOT)
            
        # Run the command and capture output
        _ = subprocess.run(
            sdist_cmd,
            check=False,
            capture_output=True,
            text=True,
            cwd=Paths.PROJECT_ROOT,
            env=env
        )
            
        # Check output directories for the tar.gz file
        for search_path in [self.output_path, Paths.get_dist_path()]:
            sdist_files = Paths.find_sdist_files(search_path)
            if sdist_files:
                # Move the file to output_dir_path if it's not already there
                if search_path != self.output_path:
                    for sdist_file in sdist_files:
                        target_file = self.output_path / sdist_file.name
                        shutil.move(str(sdist_file), str(target_file))
                        sdist_file = target_file
                    
                # Report the file
                log.info(f"Created source distribution: {sdist_file}")
                log.info(f"Size: {Paths.get_formatted_file_size(sdist_file)}")
                return

    def build(self):
        """
        Build the Ares Engine package.
        
        Raises:
            RuntimeError: If build fails
        """
        log.info(f"Using Python: {self.python_exe}")
        
        self.build_start_time = time.time()
        
        # Update the output directory path and related paths
        self.cache_path, self.build_cache_file = BuildCache.set_cache_paths(self.output_path)
        
        log.info("Using provided build configuration")
        
        # Load package configuration
        pkg_data = self.configs[ConfigType.PACKAGE].get_package_data()
        log.info(f"Loaded package configuration with {len(pkg_data)} package data entries")
        pkg_exts = self.configs[ConfigType.PACKAGE].get_extensions()
        log.info(f"Found {len(pkg_exts)} extension modules in package config")
        
        # Set up the output directory
        log.log_to_file(Paths.get_build_log_file(), f"Build started", add_timestamp=True)
        
        # Compile Cython modules
        self._compile_cmodules()
        
        # Check if we need to rebuild the wheel
        should_rebuild = self.check_for_rebuild(self.has_changed)
        
        # Check if the output directory exists
        wheel_files = Paths.find_wheel_files(self.output_path)
        
        if not should_rebuild and wheel_files:
            log.info("\nNo changes detected and wheel exists. Using existing packages.")
            
            wheel_file = wheel_files[0]
            
            log.info(f"Using existing wheel package: {wheel_file}")
            log.info(f"Size: {Paths.get_formatted_file_size(wheel_file)}")
            
            # Check for source distribution as well
            sdist_files = Paths.find_sdist_files(self.output_path)
            if sdist_files:
                sdist_file = sdist_files[0]
                log.info(f"Using existing source distribution: {sdist_file}")
                log.info(f"Size: {Paths.get_formatted_file_size(sdist_file)}")
        else:
            # Check if we need to rebuild
            if not wheel_files:
                log.info("Wheel package not found. Building new packages.")
            elif should_rebuild:
                log.info("\nChanges detected. Rebuilding packages.")
                
            # Build wheel package
            self._build_wheel()
            
            # Build source distribution
            self._build_sdist()
            
        # Calculate build duration
        self.build_duration = time.time() - self.build_start_time
        
        # Log the build results
        self.verify_wheel()
        
        # Log the build results
        BuildTelemetry.log_build_results(self.build_duration, self.output_path)

    @classmethod
    def check_engine_build(cls, build_dir=None):
        """
        Check if the engine has been built properly.
        
        Args:
            build_dir: Optional path to build directory. If None, use default engine build path.
            
        Returns:
            bool: True if the engine is built (wheel files exist), False otherwise
            
        Note:
            This method still returns a boolean as it's used externally for checking build status.
        """
        # Get the build directory from the provided path or use the default
        check_path = Path(build_dir) if build_dir is not None else Paths.get_project_paths()["ENGINE_BUILD_DIR"]
                
        # Check if the directory exists
        wheel_files = Paths.find_wheel_files(check_path)
        
        # If wheel files exist, the engine is built
        return len(wheel_files) > 0