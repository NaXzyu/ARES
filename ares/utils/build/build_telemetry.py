#!/usr/bin/env python3
"""Build telemetry and reporting functionality for Ares Engine."""

import os
from pathlib import Path
from typing import List, Tuple, Union

from ares.utils import log
from ares.utils.paths import Paths
from ares.utils.build.build_utils import BuildUtils

class BuildTelemetry:
    """Manages build telemetry and reporting for Ares Engine."""
    
    def __init__(self, build_duration: float, output_dir: Union[str, Path], 
                 build_log_file: Union[str, Path] = None):
        """Initialize build telemetry.
        
        Args:
            build_duration: Build duration in seconds
            output_dir: Output directory containing artifacts
            build_log_file: Path to the build log file (optional)
        """
        self.duration = build_duration
        self.output_path = Path(output_dir) if not isinstance(output_dir, Path) else output_dir
        self.log_file = build_log_file or Paths.get_build_log_file()
    
    @classmethod
    def log_build_completion(cls, build_log_file: Union[str, Path], build_duration: float) -> None:
        """Log build completion information to the build log file."""
        log.log_to_file(
            build_log_file,
            f"Build completed\nBuild duration: {BuildUtils.format_time(build_duration)}\nBuild artifacts:",
            add_timestamp=True,
            add_newlines=False
        )
    
    @classmethod
    def collect_artifact_info(cls, output_dir: Union[str, Path]) -> List[Tuple[str, str]]:
        """Collect information about build artifacts.
        
        Returns:
            List of tuples with (filename, formatted_size)
        """
        path = Path(output_dir) if not isinstance(output_dir, Path) else output_dir
        wheel_files = Paths.find_wheel_files(path)
        
        return [(file.name, Paths.get_formatted_file_size(file)) 
                for file in wheel_files]
    
    @classmethod
    def log_artifacts(cls, artifacts: List[Tuple[str, str]], log_level: str = "info") -> None:
        """Log artifacts list to console.
        
        Args:
            artifacts: List of tuples with (filename, formatted_size)
            log_level: Log level to use
        """
        log.log_collection(
            artifacts,
            summary_format="",
            item_format="  - {0} ({1})",
            log_level=log_level
        )
    
    @classmethod
    def log_artifacts_to_file(cls, build_log_file: Union[str, Path], artifacts: List[Tuple[str, str]]) -> bool:
        """Log artifacts list to build log file.
        
        Args:
            artifacts: List of tuples with (filename, formatted_size)
            
        Returns:
            True if successful, False otherwise
        """
        return log.log_collection_to_file(
            build_log_file,
            artifacts
        )
    
    @classmethod
    def display_build_summary(cls, duration: float, build_log_file: Union[str, Path], 
                            output_dir: Union[str, Path]) -> None:
        """Display a comprehensive build summary to console."""
        path = Path(output_dir) if not isinstance(output_dir, Path) else output_dir
        wheel_files = Paths.find_wheel_files(path)
        
        log.info("="*50)
        log.info(" BUILD SUMMARY ".center(50, "="))
        log.info("="*50)
        log.info(f"Build time:      {BuildUtils.format_time(duration)}")
        log.info(f"Build log:       {build_log_file}")
        log.info(f"Package:         {path}")
        log.info("Build artifacts:")
        for file in wheel_files:
            log.info(f"  - {file.name} ({Paths.get_formatted_file_size(file)})")
        log.info("="*50)
        
        # Add installation instructions if this is a package
        if wheel_files:
            wheel_path = wheel_files[0]
            log.info(f"To install the engine, run:")
            log.info(f"  pip install {wheel_path}")
        log.info("="*50)
    
    @classmethod
    def log_exe_summary(cls, target_exe: Union[str, Path], build_duration: float, 
                               name: str, build_log_file: Union[str, Path] = None) -> None:
        """Display and log a comprehensive executable build summary.
        
        Args:
            target_exe: Path to the built executable
            build_duration: Build duration in seconds
            name: Project/executable name
            build_log_file: Optional path to log file (if not provided, uses default)
        """
        target_exe = Path(target_exe) if not isinstance(target_exe, Path) else target_exe
        build_log_file = build_log_file or Paths.get_build_log_file()
        
        # Get executable size
        exe_size = os.path.getsize(target_exe)
        size_str = Paths.get_formatted_file_size(target_exe)
        
        # Write build summary to log
        summary_text = (
            f"Build completed\n"
            f"Build duration: {BuildUtils.format_time(build_duration)}\n"
            f"Executable size: {size_str} ({exe_size:,} bytes)\n"
            f"Project name: {name}\n"
            f"Executable path: {target_exe}"
        )
        log.log_to_file(build_log_file, summary_text, add_timestamp=True)
        
        # Display build summary
        log.info("="*50)
        log.info(" BUILD SUMMARY ".center(50, "="))
        log.info("="*50)
        log.info(f"Build time:      {BuildUtils.format_time(build_duration)}")
        log.info(f"Executable size: {size_str}")
        log.info(f"Executable path: {target_exe}")
        log.info(f"Build log:       {build_log_file}")
        log.info("="*50)
        
        # Add installation instructions if this is a package
        if "ares-" in name.lower() and target_exe.suffix in ['.whl', '.tar.gz']:
            log.info(f"To install the engine, run:")
            log.info(f"  pip install {target_exe}")
            log.info("="*50)
    
    @classmethod
    def log_build_results(cls, build_duration: float, output_dir: Union[str, Path]) -> None:
        """Log all build results and display summary.
        
        This is the main function that orchestrates all build reporting.
        """
        build_log_file = Paths.get_build_log_file()
        
        # Log completion to file
        cls.log_build_completion(build_log_file, build_duration)
        
        # Collect artifacts info
        artifacts = cls.collect_artifact_info(output_dir)
        
        # Log artifacts to console and file
        cls.log_artifacts(artifacts)
        cls.log_artifacts_to_file(build_log_file, artifacts)
        
        # Display summary
        cls.display_build_summary(build_duration, build_log_file, output_dir)
