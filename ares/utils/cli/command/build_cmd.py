"""Build command implementation for Ares Engine CLI."""

import sys
import os
from typing import Dict, Any

from ares.utils.log import log

from .command import Command
from .cmd_type import CommandType


class BuildCommand(Command):
    """Command for building the engine or projects."""
    
    @classmethod
    def get_command_type(cls) -> CommandType:
        """Get the type of this command."""
        return CommandType.BUILD
    
    @classmethod
    def execute(cls, args: Dict[str, Any]) -> int:
        """Execute the build command."""
        # Only import heavy dependencies when actually needed
        from ares.utils.const import SUCCESS, ERROR_BUILD_FAILED, ERROR_INVALID_CONFIGURATION, ENGINE_DIR_NAME
        
        print("Starting build process...")
        
        # Get build parameters
        project_path = args.get('project_path', ENGINE_DIR_NAME)
        force = args.get('force', False)
        python_path = args.get('python')  # Remove default here
        
        # Make absolutely sure we have a valid Python executable
        if python_path is None:
            python_path = sys.executable
            
        if python_path is None:  # If sys.executable is somehow None
            import shutil
            python_path = shutil.which("python") or shutil.which("python3")
            if not python_path:
                print("Error: Could not find a valid Python executable")
                return ERROR_INVALID_CONFIGURATION
                
        print(f"Using Python executable: {python_path}")
        
        # Determine what to build
        if project_path == ENGINE_DIR_NAME:
            return cls._build_engine(python_path, force)
        else:
            return cls._build_project(python_path, project_path, force)
    
    @classmethod
    def _build_engine(cls, python_path: str, force: bool) -> int:
        """Build the engine."""
        # Import dependencies only when needed
        from ares.utils.paths import Paths
        from ares.utils.build.engine_builder import EngineBuilder
        from ares.utils.const import SUCCESS, ERROR_BUILD_FAILED
        from ares.config import get_global_configs
        from ares.config.config_types import ConfigType
        
        # Initialize logging and paths
        engine_build_dir = Paths.get_project_paths()["ENGINE_BUILD_DIR"]
        print(f"Building Ares Engine into {engine_build_dir}...")
        os.makedirs(engine_build_dir, exist_ok=True)
        
        # Get configuration now that we need it
        configs = get_global_configs()
        configs[ConfigType.LOGGING].initialize(Paths.get_dev_logs_path())
        
        engine_builder = EngineBuilder(
            python_exe=python_path,
            output_dir=engine_build_dir,
            force=force,
            configs=configs
        )
        try:
            engine_builder.build()
            return SUCCESS
        except Exception as e:
            print(f"Engine build failed: {e}")
            return ERROR_BUILD_FAILED
    
    @classmethod
    def _build_project(cls, python_path: str, project_path: str, force: bool) -> int:
        """Build a project."""
        # Import dependencies only when needed
        import os
        from ares.utils.paths import Paths
        from ares.utils.build.engine_builder import EngineBuilder
        from ares.utils.build.project_builder import ProjectBuilder
        from ares.utils.const import SUCCESS, ERROR_BUILD_FAILED, ERROR_INVALID_CONFIGURATION
        from ares.config import get_global_configs
        from ares.config.config_types import ConfigType
        
        if not os.path.exists(project_path):
            print(f"Project path not found: {project_path}")
            return ERROR_INVALID_CONFIGURATION
            
        # Get configuration now that we need it
        configs = get_global_configs()
        configs[ConfigType.LOGGING].initialize(Paths.get_dev_logs_path())
        
        # First ensure the engine is built
        engine_build_dir = Paths.get_project_paths()["ENGINE_BUILD_DIR"]
        if not EngineBuilder.check_engine_build(engine_build_dir):
            print("Engine not found or incomplete. Building engine first...")
            if cls._build_engine(python_path, force) != SUCCESS:
                return ERROR_BUILD_FAILED
        
        # Initialize configs before creating builders
        configs = get_global_configs()
        if not configs:
            from ares.config import initialize
            initialize()
            configs = get_global_configs()
            
        if not configs:
            log.error("Failed to initialize configuration system")
            return ERROR_INVALID_CONFIGURATION

        # Now create the builder with initialized configs
        builder = ProjectBuilder(
            py_exe=python_path,
            project_path=project_path,
            output_dir=Paths.get_build_path(),
            force=force
        )
        
        return SUCCESS if builder.build() else ERROR_BUILD_FAILED
