"""Build script for creating projects that use the Ares engine."""

import os
from pathlib import Path

from ares.utils.build_utils import find_main_script, get_cython_module_dirs
from ares.config import initialize, project_config, build_config
from ares.build.build_exe import build_executable
from ares.utils import log
from ares.build.clean_build import clean_egg_info
from ares.build.build_state import BuildState
from ares.config.config_manager import load_project_config, load_build_config

from ares.config.logging_config import initialize_logging
initialize_logging()

FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parent.parent
BUILD_DIR = PROJECT_ROOT / "build"
ENGINE_BUILD_DIR = BUILD_DIR / "engine"
ENGINE_WHEEL_PATTERN = "ares-*.whl"

def verify_engine_availability():
    """Verify that the engine has been built."""
    # Check for wheel files
    wheel_files = list(ENGINE_BUILD_DIR.glob("ares-*.whl"))
    
    if not wheel_files:
        print("Warning: Ares engine build not found.")
        print(f"Expected to find wheel package in: {ENGINE_BUILD_DIR}")
        return False
    
    print(f"Found built engine in: {ENGINE_BUILD_DIR}")
    print(f"Engine wheel: {wheel_files[0].name}")
    return True

def build_project(py_exe, project_path, force=False, output_dir=None):
    """Build a project that uses the Ares engine."""
    log.info(f"Building project from {project_path} into {output_dir}...")
    
    # Clean egg-info directories before building to prevent PyInstaller issues
    clean_egg_info()
    
    # Convert string path to Path object if needed
    project_source_dir = Path(project_path) if project_path and not isinstance(project_path, Path) else project_path

    if not project_source_dir or not project_source_dir.exists():
        print(f"Error: Project directory not found: {project_path}")
        return False
        
    # Load custom build configuration if specified - using the centralized function
    custom_build_config = load_build_config(project_source_dir)

    # Load project configuration - using the centralized function
    config = load_project_config(project_source_dir)
    
    # Use product_name for output directory name if available and no output_dir is specified
    product_name = config.get("product_name", project_source_dir.name)
    
    # Ensure output directory exists with the product name
    if output_dir:
        build_dir = Path(output_dir)
    else:
        build_dir = BUILD_DIR / product_name
    
    # Initialize build state tracker for incremental builds
    build_state = BuildState(project_source_dir, build_dir, name=product_name)
    
    # Check if we need to rebuild
    should_rebuild, reason = build_state.should_rebuild(config)
    
    if not should_rebuild and not force:
        print(f"No changes detected. Using existing build in {build_dir}")
        print(f"Use --force to rebuild anyway.")
        return True
    
    if force:
        print(f"Forcing rebuild of project")
    else:
        print(f"Rebuilding project because: {reason}")
    
    print(f"Building project from {project_source_dir} into {build_dir}...")
    os.makedirs(build_dir, exist_ok=True)
    
    # Verify the engine is available first
    if not verify_engine_availability():
        print("Attempting to build the engine first...")
        try:
            from ares.build.build_engine import build_engine
            if not build_engine(py_exe, force, ENGINE_BUILD_DIR):
                print("Error: Failed to build the engine. Cannot continue with project build.")
                return False
        except ImportError as e:
            print(f"Error: Could not import build_engine to build the engine: {e}")
            print("Please run 'python setup.py --build' first to build the engine.")
            return False
    
    # Copy the hook files from the ares package to the project
    try:
        # Ensure we can find the hooks
        import ares.hooks
        hooks_path = Path(ares.hooks.__file__).parent
        print(f"Using Ares Engine hooks from: {hooks_path}")
        
        # Make sure we're referencing the correct hook_ares.py file
        hook_path = hooks_path / "hook_ares.py"
        if hook_path.exists():
            print(f"Found hook_ares.py at {hook_path}")
        else:
            print(f"Warning: hook_ares.py not found at {hook_path}")
    except ImportError:
        print("Warning: Could not find ares.hooks package. Runtime hooks will be generated instead.")
    
    # Find the main script by looking for entry points
    main_script = find_main_script(project_source_dir)
    if not main_script:
        print(f"Error: No entry point found in {project_source_dir}")
        print("Please make sure your Python scripts include 'if __name__ == \"__main__\":' blocks")
        return False

    print(f"Using entry point script: {main_script}")

    # Build the project executable
    try:
        # Use project name as fallback if product name is not available
        project_name = product_name if product_name else project_source_dir.name

        # Get resource directory based on config settings
        resource_dir_name = config["resource_dir_name"]
        resources_dir = project_source_dir / resource_dir_name
        if not resources_dir.exists() or not config["include_resources"]:
            resources_dir = None
        
        # Get build settings from config
        console_mode = config["console"]
        onefile_mode = config["onefile"]

        print(f"Building project executable for {project_name}...")
        print(f"  Console mode: {'enabled' if console_mode else 'disabled'}")
        print(f"  Onefile mode: {'enabled' if onefile_mode else 'disabled'}")

        success = build_executable(
            python_exe=py_exe,
            script_path=main_script,
            output_dir=build_dir,
            name=project_name,
            resources_dir=resources_dir,
            console=console_mode,
            onefile=onefile_mode
        )

        if success:
            # Update build state for incremental builds
            build_state.mark_successful_build(config)
            print(f"Project built successfully to {build_dir}")
            return True
        else:
            print(f"Failed to build project executable for {project_name}")
            return False

    except ImportError as e:
        print(f"Error: Could not build project executable - {e}")
        print("Make sure the engine is properly installed.")
        return False
