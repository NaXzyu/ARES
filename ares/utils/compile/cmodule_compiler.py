"""Cython module compiler for Ares Engine."""

import os
import sys

from ares.utils import log
from ares.utils.paths import Paths

from .compile_utils import CompileUtils

class CModuleCompiler:
    """Cython module compiler for Ares Engine."""
    
    @classmethod
    def compile(cls, python_exe=None, output_dir=None, force=False, configs=None):
        """Compile Cython modules for the project.
        
        Args:
            python_exe: Python executable to use for compilation
            output_dir: Output directory for compiled modules
            force: Force recompilation of all modules
            configs: Configuration dictionary
            
        Returns:
            bool: Whether compilation was successful
            
        Raises:
            RuntimeError: If compilation fails
        """
        # Use the current Python executable if not specified
        if not python_exe:
            python_exe = sys.executable
            
        # Use build/engine directory if not specified
        if not output_dir:
            output_dir = Paths.get_project_paths()["ENGINE_BUILD_DIR"]
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get cython module directories
        try:
            # Guard against None paths
            try:
                cython_dirs = Paths.get_cython_module_path()
                if not cython_dirs:
                    raise ValueError("No Cython module directories defined")
            except Exception as e:
                log.error(f"Error getting Cython module paths: {e}")
                cython_dirs = Paths.get_default_cython_paths()
                if not cython_dirs:
                    raise ValueError("No default Cython module directories available")
                
            # Check if modules are already compiled
            modules_exist = CompileUtils.check_modules_in_dirs(cython_dirs)
            
            # Skip compilation if modules already exist and force is False
            if modules_exist and not force:
                log.info("Compiled modules found, skipping compilation")
                return True
                
            if not modules_exist:
                log.info("No compiled modules found. Forcing compilation.")
                force = True
                
            # Get extension definitions
            extra_args = None if not configs else configs.get("compiler_args")
            extensions = CompileUtils.get_extensions(extra_args)
            
            # Check which extensions need rebuilding
            extensions_to_build = CompileUtils.check_file_changes(extensions, force)
            
            # If no extensions need rebuilding, we're done
            if not extensions_to_build:
                log.info("No changed Cython modules to build")
                return True
                
            # Log the compilation task
            log.info(f"Compiling {len(extensions_to_build)}/{len(extensions)} Cython modules...")
            
            # Generate compiler directives
            directives = CompileUtils.get_compiler_directives(configs)
            
            # Generate setup file - handle possible None return            
            setup_path = CompileUtils.generate_setup_file(extensions_to_build, directives, output_dir)
            if setup_path is None or not setup_path.exists():
                log.error("Failed to generate setup file for compilation")
                raise RuntimeError("Failed to generate setup file for compilation")
            
            # Determine build log path
            build_log = Paths.get_build_log_file()
            
            # Create build command
            build_cmd = [
                str(python_exe), 
                str(setup_path), 
                "build_ext", 
                "--inplace"
            ]
            
            # Run build command with subprocess - handle possible None values
            if setup_path and build_log:
                CompileUtils.run_subprocess(build_cmd, build_log)
            else:
                log.error("Missing setup_path or build_log, cannot proceed with compilation")
                raise RuntimeError("Missing required paths for compilation")
            
            # Verify compilation was successful
            modules_found = CompileUtils.check_compiled_modules(output_dir)
            
            return modules_found
            
        except Exception as e:
            log.error(f"Error compiling Cython modules: {e}")
            raise RuntimeError(f"Error compiling Cython modules: {e}")
