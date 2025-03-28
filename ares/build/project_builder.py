"""Build script for creating projects that use the Ares engine."""

import os
from pathlib import Path

from ares.utils.build_utils import find_main_script
from ares.build.executable_builder import ExecutableBuilder
from ares.utils import log
from ares.build.clean_build import clean_egg_info
from ares.build.build_state import BuildState
from ares.config.config_types import ConfigType
from ares.config import CONFIGS

FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parent.parent
BUILD_DIR = PROJECT_ROOT / "build"
ENGINE_BUILD_DIR = BUILD_DIR / "engine"
ENGINE_WHEEL_PATTERN = "ares-*.whl"

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
        self.py_exe = py_exe
        self.project_path = project_path
        self.output_dir = output_dir
        self.force = force
        
        # Initialize derived attributes
        self.project_source_dir = Path(project_path) if project_path and not isinstance(project_path, Path) else project_path
        
        # Setup build directory and build state
        self.product_name = CONFIGS[ConfigType.PROJECT].get_product_name()
        log.info(f"Building project: {self.product_name}")
        
        # Ensure output directory exists with the product name
        if self.output_dir:
            self.build_dir = Path(self.output_dir)
        else:
            self.build_dir = BUILD_DIR / self.product_name
            
        # Initialize build state tracker for incremental builds
        self.build_state = BuildState(self.project_source_dir, self.build_dir, name=self.product_name)

    @classmethod
    def verify_engine_availability(cls):
        """Verify that the engine has been built."""
        # Check for wheel files
        wheel_files = list(ENGINE_BUILD_DIR.glob(ENGINE_WHEEL_PATTERN))
        
        if not wheel_files:
            log.warn("Warning: Ares engine build not found.")
            log.warn(f"Expected to find wheel package in: {ENGINE_BUILD_DIR}")
            return False
        
        log.info(f"Found built engine in: {ENGINE_BUILD_DIR}")
        log.info(f"Engine wheel: {wheel_files[0].name}")
        return True
        
    def ensure_engine_built(self):
        """Ensure the engine is built and available."""
        if not ProjectBuilder.verify_engine_availability():
            log.info("Attempting to build the engine first...")
            try:
                from ares.build.build_engine import build_engine
                if not build_engine(self.py_exe, self.force, ENGINE_BUILD_DIR):
                    log.error("Error: Failed to build the engine. Cannot continue with project build.")
                    return False
            except ImportError as e:
                log.error(f"Error: Could not import build_engine to build the engine: {e}")
                log.error("Please run 'python setup.py --build' first to build the engine.")
                return False
        return True
        
    def check_for_changes(self):
        """Check if we need to rebuild the project."""
        # Get build configuration
        build_config = CONFIGS[ConfigType.BUILD].get_override_dict()
        package_config = CONFIGS[ConfigType.PACKAGE].get_override_dict()
        
        # Combine configurations to ensure we detect all relevant changes
        combined_config = {**build_config, **package_config}
        
        # Import helper to preprocess config objects
        from ares.build.build_cache import _preprocess_paths_for_json
        
        # Make sure we process the config for any Path objects before checking
        processed_config = _preprocess_paths_for_json(combined_config)
        
        # Check if rebuild is needed with the processed config
        should_rebuild, reason = self.build_state.should_rebuild(processed_config)
        
        if not should_rebuild and not self.force:
            log.info(f"No changes detected. Using existing build in {self.build_dir}")
            log.info(f"Use --force to rebuild anyway.")
            return False
        
        if self.force:
            log.info(f"Forcing rebuild of project")
        else:
            log.info(f"Rebuilding project because: {reason}")
            
        return True
    
    def build(self):
        """Build the project using the Ares Engine."""
        log.info(f"Building project from {self.project_path} into {self.output_dir or BUILD_DIR}...")
        
        # Clean egg-info directories before building to prevent PyInstaller issues
        clean_egg_info()
        
        if not self.project_source_dir or not self.project_source_dir.exists():
            log.error(f"Error: Project directory not found: {self.project_path}")
            return False
            
        # Get module directories from cython_compiler
        from ares.build.cython_compiler import get_cython_module_dirs
        cython_module_dirs = get_cython_module_dirs()
        if cython_module_dirs:
            # First log the total count
            log.info(f"Found {len(cython_module_dirs)} extension source directories:")
            # Then log each directory individually with its description
            for module_path, description in cython_module_dirs:
                log.info(f"  - {description}: {module_path}")
        
        # Check for extension directories
        extension_dirs = [d for d in self.project_source_dir.iterdir() if d.is_dir() and (d / "extensions").exists()]
        if extension_dirs:
            log.info(f"Found {len(extension_dirs)} project extension directories:")
            for dir_path in extension_dirs:
                log.info(f"  - Project extension: {dir_path}")
        else:
            log.info("No project extension directories found")
        
        # Check if we need to rebuild
        if not self.check_for_changes():
            return True
            
        # Ensure build directory exists
        log.info(f"Building project from {self.project_source_dir} into {self.build_dir}...")
        os.makedirs(self.build_dir, exist_ok=True)
        
        # Verify the engine is available first
        if not self.ensure_engine_built():
            return False
        
        # Check for hooks
        try:
            # Ensure we can find the hooks
            import ares.hooks
            hooks_path = Path(ares.hooks.__file__).parent
            log.info(f"Using Ares Engine hooks from: {hooks_path}")
            
            # Make sure we're referencing the correct hook_ares.py file
            hook_path = hooks_path / "hook_ares.py"
            if (hook_path).exists():
                log.info(f"Found hook_ares.py at {hook_path}")
            else:
                log.warn(f"Warning: hook_ares.py not found at {hook_path}")
        except ImportError:
            log.warn("Warning: Could not find ares.hooks package. Runtime hooks will be generated instead.")
        
        # Find the main script by looking for entry points
        main_script = find_main_script(self.project_source_dir)
        if not main_script:
            log.error(f"Error: No entry point found in {self.project_source_dir}")
            log.error("Please make sure your Python scripts include 'if __name__ == \"__main__\":' blocks")
            return False

        log.info(f"Using entry point script: {main_script}")

        # Build the project executable
        try:
            # Use product name from config - already loaded with potential overrides
            product_name = self.product_name
            
            # Get resource directory based on config settings
            resource_dir_name = CONFIGS[ConfigType.BUILD].get_resource_dir_name()
            resources_dir = self.project_source_dir / resource_dir_name
            if not resources_dir.exists() or not CONFIGS[ConfigType.BUILD].should_include_resources():
                resources_dir = None
            
            log.info(f"Building project executable for {product_name}...")
            log.info(f"  Console mode: {'enabled' if CONFIGS[ConfigType.PACKAGE].is_console_enabled() else 'disabled'}")
            log.info(f"  Onefile mode: {'enabled' if CONFIGS[ConfigType.PACKAGE].is_onefile_enabled() else 'disabled'}")

            # Use ExecutableBuilder.create to build the executable
            success = ExecutableBuilder.create(
                python_exe=self.py_exe,
                script_path=main_script,
                output_dir=self.build_dir,
                name=product_name,  # Using product_name here ensures consistent naming
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
                log.info(f"Project built successfully to {self.build_dir}")
                return True
            else:
                log.error(f"Failed to build project executable for {product_name}")
                return False

        except ImportError as e:
            log.error(f"Error: Could not build project executable - {e}")
            log.error("Make sure the engine is properly installed.")
            return False
