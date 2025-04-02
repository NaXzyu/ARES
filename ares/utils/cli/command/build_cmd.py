"""Build command implementation for Ares Engine CLI."""

import sys
import os
from typing import Dict, Any

from .command import Command
from .cmd_type import CommandType
from ares.utils.paths import Paths
from ares.utils.log import log
from ares.config import get_global_configs
from ares.config.config_types import ConfigType
from ares.utils.build.engine_builder import EngineBuilder
from ares.utils.build.project_builder import ProjectBuilder
from ares.utils.const import (
    SUCCESS, ERROR_BUILD_FAILED, 
    ERROR_INVALID_CONFIGURATION, 
    ENGINE_DIR_NAME,
)

class BuildCommand(Command):
    """Command for building the engine or projects."""
    
    @classmethod
    def get_command_type(cls) -> CommandType:
        """Get the type of this command."""
        return CommandType.BUILD
    
    @classmethod
    def execute(cls, args: Dict[str, Any]) -> int:
        """Execute the build command."""
        # Get configuration
        CONFIGS = get_global_configs()
        CONFIGS[ConfigType.LOGGING].initialize(Paths.get_dev_logs_path())
        
        # Get build parameters
        project_path = args.get('project_path', ENGINE_DIR_NAME)
        force = args.get('force', False)
        python_path = args.get('python', sys.executable)
        
        log.info(f"Using Python executable: {python_path}")
        
        # Determine what to build
        if project_path == ENGINE_DIR_NAME:
            return cls._build_engine(python_path, force, CONFIGS)
        else:
            return cls._build_project(python_path, project_path, force, CONFIGS)
    
    @classmethod
    def _build_engine(cls, python_path: str, force: bool, configs: Dict) -> int:
        """Build the engine."""
        engine_build_dir = Paths.get_project_paths()["ENGINE_BUILD_DIR"]
        log.info(f"Building Ares Engine into {engine_build_dir}...")
        os.makedirs(engine_build_dir, exist_ok=True)
        
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
            log.error(f"Engine build failed: {e}")
            return ERROR_BUILD_FAILED
    
    @classmethod
    def _build_project(cls, python_path: str, project_path: str, force: bool, configs: Dict) -> int:
        """Build a project."""
        if not os.path.exists(project_path):
            log.error(f"Project path not found: {project_path}")
            return ERROR_INVALID_CONFIGURATION
            
        # First ensure the engine is built
        engine_build_dir = Paths.get_project_paths()["ENGINE_BUILD_DIR"]
        if not EngineBuilder.check_engine_build(engine_build_dir):
            log.info("Engine not found or incomplete. Building engine first...")
            if cls._build_engine(python_path, force, configs) != SUCCESS:
                return ERROR_BUILD_FAILED
        
        # Build the project
        builder = ProjectBuilder(
            py_exe=python_path,
            project_path=project_path,
            output_dir=Paths.get_build_path(),
            force=force
        )
        return SUCCESS if builder.build() else ERROR_BUILD_FAILED
