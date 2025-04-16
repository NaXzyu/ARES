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
from ares.utils.build.build_utils import BuildUtils
from ares.utils.compile import CModuleCompiler
from ares.utils.compile.compile_utils import CompileUtils
from ares.utils.const import PYTHON_EXT, SETUP_FILE_NAME
from ares.utils.paths import Paths

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
                
            current_hash = BuildUtils.compute_file_hash(py_file)
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
            current_hash = BuildUtils.compute_file_hash(setup_py)
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
        
        # Use CModuleCompiler directly with correct parameter order:
        # python_exe, output_dir, force, configs
        if not CModuleCompiler.compile(self.python_exe, self.output_dir, self.force, self.configs):
            raise RuntimeError("Failed to compile Cython modules. Cannot continue with build.")
        
        # Check if the cache file exists
        self.has_changed = self.cache.check_and_reset_rebuild_status()
        
        log.info("Compilation complete.")
    
    @classmethod
    def _build_wheel(cls, output_dir, configs=None, python_exe=None):
        """Build wheel package for distribution.
        
        Args:
            output_dir: Directory where wheel should be built
            configs: Configuration dictionary
            python_exe: Python executable path
            
        Returns:
            Path: Path to the built wheel file
            
        Raises:
            RuntimeError: If wheel build fails or executable not found
        """
        log.info("Building wheel package...")
        
        # Handle case where python_exe is None - use current Python interpreter
        if python_exe is None:
            python_exe = sys.executable or shutil.which("python") or shutil.which("python3")
            if not python_exe:
                log.error("Could not determine Python executable path")
                raise RuntimeError("Could not determine Python executable path")
            log.info(f"No Python executable specified, using: {python_exe}")
        # Verify Python executable exists
        if not os.path.exists(str(python_exe)):
            log.error(f"Python executable not found: {python_exe}")
            raise RuntimeError(f"Python executable not found: {python_exe}")
        if output_dir is None:
            log.error("Output directory cannot be None")
            raise RuntimeError("Output directory cannot be None")
        output_dir_str = str(output_dir)
        current_dir = os.getcwd()
        os.chdir(str(Paths.PROJECT_ROOT))
        try:
            os.makedirs(output_dir_str, exist_ok=True)
            build_cmd = [
                str(python_exe), "-m", "pip", "wheel",
                "--wheel-dir", output_dir_str,
                "." # Include all dependencies in the current directory
            ]
            for i, item in enumerate(build_cmd):
                if item is None:
                    log.error(f"Build command element {i} is None")
                    raise RuntimeError(f"Build command contains None value at position {i}")
            build_log = Paths.get_build_log_file()
            log.info(f"Running wheel build command: {' '.join(build_cmd)}")
            log.info(f"Build output directory: {output_dir_str}")
            process = subprocess.Popen(
                build_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            error_lines = log.track_process_output(
                process=process,
                log_file_path=build_log,
                error_keywords=['error:', 'exception:', 'failed', 'warning:'],
                print_errors=True
            )
            ret_code = process.wait()
            if ret_code != 0:
                log.error(f"Wheel build failed with return code {ret_code}")
                if error_lines:
                    log.display_error_details(error_lines, header="Wheel build errors:")
                raise RuntimeError(f"Wheel build failed with return code {ret_code}")
            wheel_files = Paths.find_wheel_files(output_dir)
            if not wheel_files:
                dist_dir = Paths.get_dist_path()
                if dist_dir.exists():
                    log.info(f"No wheel found in {output_dir_str}; checking {dist_dir}")
                    wheel_files = Paths.find_wheel_files(dist_dir)
                    if wheel_files:
                        for wf in wheel_files:
                            target = Path(output_dir) / wf.name
                            log.info(f"Moving wheel file {wf} -> {target}")
                            shutil.move(str(wf), str(target))
                        wheel_files = Paths.find_wheel_files(output_dir)
                        if not any(dist_dir.iterdir()):
                            dist_dir.rmdir()
                            log.info(f"Removed empty dist directory: {dist_dir}")
            if not wheel_files:
                log.error(f"No wheel file found in {output_dir_str} or {Paths.get_dist_path()}")
                if error_lines:
                    log.display_error_details(error_lines, header="Wheel build errors:")
                raise RuntimeError("No wheel file found after build")
            wheel_file_path = wheel_files[0]
            log.info(f"Successfully built wheel: {wheel_file_path.name}")
            log.info(f"Wheel size: {Paths.get_formatted_file_size(wheel_file_path)}")

            # Remove leftover setup.py from the engine build directory using Paths API
            engine_build_dir = Paths.get_engine_build_dir()
            setup_file = engine_build_dir / "setup.py"
            if setup_file.exists():
                setup_file.unlink()
                log.info(f"Removed leftover setup.py from {setup_file}")

            return wheel_file_path
        except Exception as e:
            log.error(f"Error building wheel: {str(e)}")
            raise RuntimeError(f"Error building wheel: {str(e)}")
        finally:
            os.chdir(current_dir)

    def build(self):
        log.info(f"Using Python: {self.python_exe}")

        self.build_start_time = time.time()

        # Update the cache paths based on output_dir
        self.cache_path, self.build_cache_file = BuildCache.set_cache_paths(self.output_dir)
        # Ensure self.output_path is set
        if self.output_path is None:
            self.output_path = self.output_dir

        # Log the build paths 
        log.log_build_paths(self.output_path, self.cache_path, self.build_cache_file)
        
        # Load package configuration
        pkg_data = self.configs[ConfigType.PACKAGE].get_package_data()
        log.info(f"Loaded package configuration with {len(pkg_data)} package data entries")
        # Use CompileUtils instead of self.configs[ConfigType.PACKAGE]
        pkg_exts = CompileUtils.get_extensions()
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
        else:
            # Check if we need to rebuild
            if not wheel_files:
                log.info("Wheel package not found. Building new packages.")
            elif should_rebuild:
                log.info("\nChanges detected. Rebuilding packages.")
            # Make sure we have a valid Python executable
            python_exe_to_use = self.python_exe or sys.executable
            try:
                self._build_wheel(self.output_path, self.configs, python_exe_to_use)
            except Exception as e:
                log.error(f"Error during wheel build: {str(e)}")
                raise RuntimeError(f"Error during wheel build: {str(e)}")
        
        # Calculate build duration
        self.build_duration = time.time() - self.build_start_time
        
        # Log the build results
        self.verify_wheel()
        BuildTelemetry.log_build_results(self.build_duration, self.output_path)

    @classmethod
    def check_engine_build(cls, build_dir=None):
        """
        Check if the engine has been built properly. (with required arguments)
        
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
        if not check_path.exists():
            return False
        
        # Check for wheel files in the directory
        wheel_files = Paths.find_wheel_files(check_path)
        
        return len(wheel_files) > 0