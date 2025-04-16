#!/usr/bin/env python3
"""Build script for creating standalone executables from Ares Engine projects."""

import os
import shutil
import subprocess
import time
from pathlib import Path

from ares.utils import log
from ares.utils.build.build_cleaner import BuildCleaner
from ares.utils.build.build_telemetry import BuildTelemetry
from ares.utils.hook.hook_manager import HookManager
from ares.utils.paths import Paths
from ares.utils.spec.exe_spec import ExeSpec
from ares.utils.build.build_utils import BuildUtils
from ares.utils.const import ERROR_BUILD_FAILED, ERROR_MISSING_DEPENDENCY
from ares.utils.compile.compile_utils import CompileUtils  # Add import for CompileUtils

class ExeBuilder:
    """Builds standalone executables from Python scripts using PyInstaller."""

    def __init__(self, python_exe, output_dir, main_script, name=None, resources_dir=None, console_mode=True, onefile=True):
        """Initialize the executable builder."""
        self.py_exe = str(python_exe)
        self.output_path = Path(output_dir)
        self.main_script = Path(main_script)
        
        # Store the name parameter as an instance attribute
        self.name = name if name else self.main_script.stem
        
        self.resources_dir = Path(resources_dir) if resources_dir else None
        self.console_mode = console_mode
        self.onefile = onefile

        # Get configs only when we need them
        from ares.config import get_global_configs
        from ares.config.config_types import ConfigType
        
        configs = get_global_configs()
        if not configs:
            log.error("Configuration system not initialized")
            raise RuntimeError("Configuration system not initialized")

        # Get package data from config using CONFIGS dictionary
        self.package_data = configs[ConfigType.PACKAGE].get_package_data()
        # Use CompileUtils instead of configs[ConfigType.PACKAGE]
        self.extensions = CompileUtils.get_extensions()
        
        # Platform-specific attributes for file extension
        self.executable_extension = '.exe' if BuildUtils.is_windows() else ''

        # Tracking variables
        self.build_start_time = None
        self.build_duration = None

    def build(self):
        """Build the executable using PyInstaller."""
        try:
            # Clean egg-info to avoid permission issues
            BuildCleaner.clean_egg_info()

            self.build_start_time = time.time()

            # Start build log using log_to_file method
            log.log_to_file(
                Paths.get_build_log_file(),
                f"Build started\nProject name: {self.name}\nMain script: {self.main_script}\nOutput directory: {self.output_path}",
                add_timestamp=True
            )

            log.info(f"Building {self.name} executable from {self.main_script}")

            # Ensure PyInstaller is installed
            try:
                subprocess.run(
                    [self.py_exe, "-c", "import PyInstaller"],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                log.info("PyInstaller not found. Installing...")
                try:
                    subprocess.run(
                        [self.py_exe, "-m", "pip", "install", "pyinstaller"],
                        check=True
                    )
                except subprocess.CalledProcessError as e:
                    log.error(f"Failed to install PyInstaller: {e}")
                    return False

            # Find SDL2 DLLs and Cython binaries
            bins = BuildUtils.find_sdl2_dlls(self.py_exe, log.info)
            cbins = BuildUtils.find_cython_binaries(Paths.PROJECT_ROOT)
            bins.extend(cbins)

            # Validate hooks using the BuildUtils method
            hooks = BuildUtils.validate_hooks(self.output_path)
            if not hooks:
                return False

            # Use Paths.get_executable_output_path to get the output directory
            out_path = Paths.get_executable_output_path(self.output_path)

            # Create a spec file using the SpecBuilder class
            try:
                exe_spec = ExeSpec(
                    output_dir=self.output_path,
                    main_script=self.main_script,
                    name=self.name,
                    resources_dir=self.resources_dir,
                    console_mode=self.console_mode,
                    onefile=self.onefile
                )
                spec_file = exe_spec.apply(binaries=bins, hook_files=hooks)
            except AttributeError as e:
                log.error(f"Error creating spec file: {e}")
                # Provide more specific error for common issues
                if "get_hooks_dir" in str(e):
                    log.error("Hook configuration error. Check that Paths.get_hooks_path() is properly configured.")
                return False
            except Exception as e:
                log.error(f"Error creating spec file: {e}")
                return False

            if not spec_file:
                log.error("Error: Failed to create spec file")
                return False

            # Build PyInstaller command using the spec file
            pyinstaller_cmd = [
                self.py_exe, "-m", "PyInstaller",
                str(spec_file),
                "--clean",
                "--distpath", str(out_path),  # Use out subdirectory for output
                "--workpath", str(self.output_path / "temp")  # Use temp directory
            ]

            # Log the command
            log.info("Running PyInstaller with spec file:")
            log.info(f"  {' '.join(map(str, pyinstaller_cmd))}")

            # Run PyInstaller
            try:
                # Capture PyInstaller output with detailed error handling
                process = subprocess.Popen(
                    pyinstaller_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                error_lines = log.track_process_output(
                    process=process,
                    log_file_path=Paths.get_build_log_file(),
                    error_keywords=['error:', 'exception:', 'traceback', 'fail', 'warning:', 'nameerror'],
                    max_error_lines=10,
                    print_errors=True
                )

                # Wait for process to complete
                ret_code = process.wait()
                if ret_code != 0:
                    log.display_error_details(
                        error_lines, 
                        header="Error details from PyInstaller:",
                        max_lines=5
                    )
                    # Check for specific error signatures in the output
                    if any("AttributeError: type object 'Paths' has no attribute 'get_hooks_dir'" in line for line in error_lines):
                        log.error("PyInstaller spec file is using an incorrect Paths method. Check spec file template.")
                        return False
                    raise RuntimeError(f"PyInstaller failed with return code {ret_code}")
            except subprocess.CalledProcessError as e:
                log.log_error_output(e, Paths.get_build_log_file())
                return False

            # Get the executable path from the out subdirectory
            executable_name = f"{self.name}{self.executable_extension}"
            target_exe = out_path / executable_name

            # Log name information for debugging
            log.info(f"Building executable with name: {self.name}")
            log.info(f"Expected executable: {target_exe}")

            if target_exe.exists():
                # Calculate build telemetry
                build_end_time = time.time()
                self.build_duration = build_end_time - self.build_start_time

                # Use BuildTelemetry to log executable summary
                BuildTelemetry.log_exe_summary(
                    target_exe=target_exe,
                    build_duration=self.build_duration,
                    name=self.name
                )

                # Clean up PyInstaller artifacts
                build_temp_dir = self.output_path / "temp"
                if build_temp_dir.exists():
                    shutil.rmtree(build_temp_dir)

                return True
            else:
                log.error(f"Error: Expected executable not found at {target_exe}")
                return False
        except Exception as e:
            log.error(f"Build failed: {e}")
            return False

    @classmethod
    def create(cls, python_exe, script_path, output_dir, name=None, resources_dir=None, console_mode=True, onefile=True):
        """Factory method to create and build an executable in one step."""
        # Clean egg-info first to prevent permission issues
        BuildCleaner.clean_egg_info()

        builder = cls(
            python_exe=python_exe,
            output_dir=output_dir,
            main_script=script_path,
            name=name,
            resources_dir=resources_dir,
            console_mode=console_mode,
            onefile=onefile
        )

        return builder.build()
