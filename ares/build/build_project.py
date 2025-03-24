"""Build script for creating projects that use the Ares engine."""

import os
import configparser
from pathlib import Path

from ares.utils.build_utils import find_main_script
from ares.config import initialize, project_config, build_config
from ares.build.build_exe import build_executable
from ares.utils import log
from ares.build.clean_build import clean_egg_info

from ares.config.logging_config import initialize_logging
initialize_logging()

FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parent.parent
BUILD_DIR = PROJECT_ROOT / "build"
ENGINE_BUILD_DIR = BUILD_DIR / "engine"
ENGINE_WHEEL_PATTERN = "ares-*.whl"

def load_project_config(project_path):
    """Load project configuration, prioritizing local project.ini if it exists."""
    # Initialize default config first
    initialize()
    
    # Check if the project has its own project.ini
    local_project_ini = Path(project_path) / "project.ini"
    
    if local_project_ini.exists():
        print("\n== Using project-specific configuration ==")
        print(f"Location: {local_project_ini}")
        
        # Load the local project.ini
        local_config = configparser.ConfigParser()
        local_config.read(local_project_ini)
        
        # Override the global project_config with local settings
        # We'll return these settings as a dictionary so we don't modify the global config
        config_values = {
            "console": local_config.getboolean("project", "console", fallback=project_config.is_console_enabled()),
            "onefile": local_config.getboolean("project", "onefile", fallback=project_config.is_onefile_enabled()),
            "include_resources": local_config.getboolean("resources", "include_resources", 
                                             fallback=project_config.getboolean("resources", "include_resources", True)),
            "resource_dir_name": local_config.get("resources", "resource_dir_name", 
                                      fallback=project_config.get("resources", "resource_dir_name", "resources")),
            # Get product_name now from build_config instead, but check local project.ini first
            "product_name": (
                local_config.get("package", "product_name", fallback=None) 
                or build_config.get_product_name()
            )
        }
    else:
        print("\n== Using default project configuration ==")
        try:
            # Guard against project_config being None
            config_path = str(project_config.user_path) if project_config and hasattr(project_config, 'user_path') else "global defaults"
            print(f"Location: {config_path}")
        except (AttributeError, TypeError):
            print("Location: <default configuration>")
            
        # Use global settings with safe defaults in case project_config is not fully initialized
        if project_config and build_config:
            config_values = {
                "console": project_config.is_console_enabled(),
                "onefile": project_config.is_onefile_enabled(),
                "include_resources": project_config.getboolean("resources", "include_resources", True),
                "resource_dir_name": project_config.get("resources", "resource_dir_name", "resources"),
                # Product name now comes from build_config
                "product_name": build_config.get_product_name()
            }
        else:
            # Even when configs are not initialized, try to use build_config values as fallback defaults
            # This makes the defaults consistent with our INI files
            print("Warning: Project configuration is not initialized. Using default configuration values.")
            try:
                # Try to load basic values from build.ini directly if possible
                from ares.config.config import config
                build_ini = config.load("build")
                fallback_product_name = build_ini.get("package", "product_name", "Ares") if build_ini else "Ares"
            except Exception:
                # If we can't load from build.ini, use hardcoded fallback that matches build.ini default
                fallback_product_name = "Ares"
            
            config_values = {
                "console": True,
                "onefile": True, 
                "include_resources": True,
                "resource_dir_name": "resources",
                "product_name": fallback_product_name
            }
        
    return config_values

# Add this function to load custom build config if specified
def load_build_config(project_path):
    """Load build configuration, checking for project-specific references."""
    from ares.config import initialize, project_config, config
    
    initialize()
    
    # Check if the project has its own project.ini
    local_project_ini = Path(project_path) / "project.ini"
    build_config_file = "build.ini"  # Default
    
    if local_project_ini.exists():
        local_config = configparser.ConfigParser()
        local_config.read(local_project_ini)
        
        # Check for custom build config file
        if local_config.has_option("project", "build_config_file"):
            build_config_file = local_config.get("project", "build_config_file")
    else:
        # Check if project_config is properly initialized
        if project_config is not None and hasattr(project_config, 'get_build_config_file'):
            try:
                build_config_file = project_config.get_build_config_file()
            except (AttributeError, TypeError):
                # Fall back to default
                build_config_file = "build.ini"
    
    # Check if the specified build config exists in the project directory
    custom_build_config = Path(project_path) / build_config_file
    if custom_build_config.exists():
        return config.load(custom_build_config.stem)
    
    # Fall back to default build config
    return config.load("build")

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
        
    # Load custom build configuration if specified
    custom_build_config = load_build_config(project_source_dir)

    # Load project configuration (either local or default) first to get product_name
    config = load_project_config(project_source_dir)
    
    # Use product_name for output directory name if available and no output_dir is specified
    product_name = config.get("product_name", project_source_dir.name)
    
    # Ensure output directory exists with the product name
    if output_dir:
        build_dir = Path(output_dir)
    else:
        # Use product_name instead of hardcoded "project"
        build_dir = BUILD_DIR / product_name
    
    print(f"Building project from {project_source_dir} into {build_dir}...")
    os.makedirs(build_dir, exist_ok=True)
    
    # Verify the engine is available first
    if not verify_engine_availability():
        print("Attempting to build the engine first...")
        try:
            # Use the build_engine function from the parent module
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
        if (hook_path.exists()):
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
            print(f"Project built successfully to {build_dir}")
            return True
        else:
            print(f"Failed to build project executable for {project_name}")
            return False

    except ImportError as e:
        print(f"Error: Could not build project executable - {e}")
        print("Make sure the engine is properly installed.")
        return False
