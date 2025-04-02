"""Build script for creating projects that use the Ares engine."""

import os

from ares.config import CONFIGS
from ares.config.config_types import ConfigType
from ares.utils import log
from ares.utils.build.build_cleaner import BuildCleaner
from ares.utils.build.build_state import BuildState
from ares.utils.build.build_cache import BuildCache
from ares.utils.build.exe_builder import ExeBuilder
from ares.utils.build.utils import find_main_script
from ares.utils.paths import Paths
from ares.utils.const import ENGINE_WHEEL_PATTERN

class ProjectBuilder:
    """Builds Ares Engine projects."""
    
    def __init__(self, py_exe, project_path, output_dir=None, force=False):
        """Initialize the project builder.
        
        Args:
            py_exe: Path to Python executable to use for building
            project_path: Path to the project source directory
            output_dir: Output directory for build artifacts (optional)
            force: Whether to force a rebuild even if no changes detected
        """
        # Store only the minimum required state
        self.py_exe = py_exe
        self.force = force
        self.project_path = project_path
        self.output_dir = output_dir
        
        # Setup build state
        self.product_name = CONFIGS[ConfigType.PROJECT].get_product_name()
        log.info(f"Building project: {self.product_name}")
        
        # Initialize build state tracker for incremental builds using Paths API directly
        self.build_state = BuildState(
            Paths.get_project_source_path(project_path),
            Paths.get_project_build_path(self.product_name, output_dir), 
            name=self.product_name
        )

    @classmethod
    def verify_engine_availability(cls):
        """Verify that the engine has been built."""
        # Get engine build directory from Paths API
        engine_build_dir = Paths.get_project_paths()["ENGINE_BUILD_DIR"]
        
        # Find wheel files using Paths API and ENGINE_WHEEL_PATTERN constant
        wheel_files = Paths.find_files(engine_build_dir, ENGINE_WHEEL_PATTERN)
        
        if not wheel_files:
            log.warn("Warning: Ares engine build not found.")
            log.warn(f"Expected to find wheel package in: {engine_build_dir}")
            return False
        
        log.info(f"Found built engine in: {engine_build_dir}")
        log.info(f"Engine wheel: {wheel_files[0].name}")
        return True
        
    def ensure_engine_built(self):
        """Ensure the engine is built and available."""
        engine_build_dir = Paths.get_project_paths()["ENGINE_BUILD_DIR"]
        
        if not ProjectBuilder.verify_engine_availability():
            log.info("Attempting to build the engine first...")
            try:
                from ares.utils.build.engine_builder import EngineBuilder
                from ares.config import CONFIGS
                
                builder = EngineBuilder(
                    python_exe=self.py_exe,
                    output_dir=engine_build_dir,
                    force=self.force,
                    configs=CONFIGS
                )
                builder.build()
            except ImportError as e:
                raise RuntimeError(f"Could not import EngineBuilder to build the engine: {e}.")
        return True
        
    def check_for_changes(self):
        """Check if we need to rebuild the project."""
        # Get build configuration
        build_config = CONFIGS[ConfigType.BUILD].get_override_dict()
        package_config = CONFIGS[ConfigType.PACKAGE].get_override_dict()
        
        # Combine configurations to ensure we detect all relevant changes
        combined_config = {**build_config, **package_config}
        
        # Use BuildCache class to preprocess config for JSON serialization
        build_cache = BuildCache.get_instance()
        processed_config = build_cache._preprocess_paths_for_json(combined_config)
        
        # Check if rebuild is needed with the processed config
        should_rebuild, reason = self.build_state.should_rebuild(processed_config)
        
        if not should_rebuild and not self.force:
            build_dir = Paths.get_project_build_path(self.product_name, self.output_dir)
            log.info(f"No changes detected. Using existing build in {build_dir}")
            log.info(f"Use --force to rebuild anyway.")
            return False
        
        if self.force:
            log.info(f"Forcing rebuild of project")
        else:
            log.info(f"Rebuilding project because: {reason}")
            
        return True
    
    def build(self):
        """Build the project using the Ares Engine."""
        # Get project source and build directories using Paths API directly
        project_source_dir = Paths.get_project_source_path(self.project_path)
        build_dir = Paths.get_project_build_path(self.product_name, self.output_dir)
        
        log.info(f"Building project from {project_source_dir} into {build_dir}...")
        
        # Clean egg-info directories before building to prevent PyInstaller issues
        BuildCleaner.clean_egg_info()
        
        if not project_source_dir or not project_source_dir.exists():
            raise RuntimeError(f"Error: Project directory not found: {self.project_path}")
            
        # Get Cython module directories using Paths API
        cython_module_dirs = Paths.get_cython_module_path()
        log.log_collection(
            cython_module_dirs, 
            summary_format="Found {count} extension source directories:",
            item_format="  - {1}: {0}"
        )
        
        # Check for extension directories using Paths API
        extension_dirs = Paths.find_extension_paths(project_source_dir)
        log.log_collection(
            extension_dirs,
            summary_format="Found {count} project extension directories:", 
            item_format="  - Project extension: {item}"
        )
        
        # Check if we need to rebuild
        if not self.check_for_changes():
            return True
            
        # Create build directory
        log.info(f"Building project from {project_source_dir} into {build_dir}...")
        os.makedirs(build_dir, exist_ok=True)
        
        # Verify the engine is available first
        if not self.ensure_engine_built():
            return False
        
        # Use Paths API to get hooks directory and files
        hooks_dir = Paths.get_hooks_path()
        log.info(f"Using Ares Engine hooks from: {hooks_dir}")
            
        # Make sure we're referencing the correct hook_ares.py file
        hook_path = Paths.get_hook_file("hook_ares")
        if hook_path.exists():
            log.info(f"Found hook_ares.py at {hook_path}")
        else:
            raise RuntimeError(f"hook_ares.py not found at {hook_path}")
        
        # Find the main script by looking for entry points
        main_script = find_main_script(project_source_dir)
        if not main_script:
            raise RuntimeError(f"Error: No entry point found in {project_source_dir}. ")

        # Build the project executable
        log.info(f"Using entry point script: {main_script}")
        try:
            # Get resource directory path using Paths API
            resources_dir = None
            if CONFIGS[ConfigType.BUILD].should_include_resources():
                resource_dir_name = CONFIGS[ConfigType.BUILD].get_resource_dir_name()
                resources_dir = Paths.get_resources_path(self.project_path, resource_dir_name)
            
            log.info(f"Building project executable for {self.product_name}...")
            log.info(f"  Console mode: {'enabled' if CONFIGS[ConfigType.PACKAGE].is_console_enabled() else 'disabled'}")
            log.info(f"  Onefile mode: {'enabled' if CONFIGS[ConfigType.PACKAGE].is_onefile_enabled() else 'disabled'}")

            # Use ExecutableBuilder.create to build the executable
            success = ExeBuilder.create(
                python_exe=self.py_exe,
                script_path=main_script,
                output_dir=build_dir,
                name=self.product_name,  # Using product_name here ensures consistent naming
                resources_dir=resources_dir,
                console_mode=CONFIGS[ConfigType.PACKAGE].is_console_enabled(),
                onefile=CONFIGS[ConfigType.PACKAGE].is_onefile_enabled()
            )

            if success:
                # Combine build and package configurations for state tracking
                build_config = CONFIGS[ConfigType.BUILD].get_override_dict()
                package_config = CONFIGS[ConfigType.PACKAGE].get_override_dict()
                combined_config = {**build_config, **package_config}
                
                # Update build state for incremental builds
                self.build_state.mark_successful_build(combined_config)
                log.info(f"Project built successfully to {build_dir}")
                return True
            else:
                log.error(f"Failed to build project executable for {self.product_name}")
                return False

        except ImportError as e:
            log.error(f"Error: Could not build project executable - {e}")
            log.error("Make sure the engine is properly installed.")
            return False
