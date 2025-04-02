"""Module compiler for handling Cython module compilation in Ares Engine."""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

from ares.utils.const import ERROR_BUILD_FAILED, SUCCESS
from ares.utils.log import log
from ares.utils.paths import Paths
from ares.utils.build.build_cache import BuildCache

from .cmodule_manager import CModuleManager
from .ext_manager import ExtManager
from .utils import (
    filter_compiler_flags,
    generate_setup_file,
    get_compiler_directives,
    run_subprocess,
)

class CModuleCompiler:
    """Handles compilation of Cython modules for Ares Engine."""
    
    @classmethod
    def _run_build_process(cls, 
                          python_exe: Union[str, Path], 
                          extensions_to_build: List[Any], 
                          compiler_directives: Dict[str, Any], 
                          build_args: List[str], 
                          build_log_path: Path) -> int:
        """Run the build process for Cython extensions.
        
        Returns:
            int: Status code (SUCCESS or ERROR_BUILD_FAILED)
        """
        temp_setup = Paths.get_cache_path() / "temp_setup.py"
        
        try:
            generate_setup_file(extensions_to_build, compiler_directives, temp_setup)
            
            if extensions_to_build:
                run_cmd = [str(python_exe), str(temp_setup)]
                run_cmd.extend(build_args)
            
                run_subprocess(run_cmd, build_log_path)
                
                # Use the BuildCache class instead of direct functions
                build_cache = BuildCache.get_instance()
                build_cache.cache["rebuilt_modules"] = True
                build_cache.save()
                
                return SUCCESS
            return SUCCESS  # No extensions to build is still a success
        except Exception as e:
            log.error(f"Error during build process: {e}")
            return ERROR_BUILD_FAILED
        finally:
            if temp_setup.exists():
                os.unlink(temp_setup)
    
    @classmethod
    def compile(cls, 
                python_exe: Union[str, Path], 
                build_dir: Path, 
                build_log_path: Path, 
                force: bool = False) -> bool:
        """Compile the Cython modules for the project."""
        from Cython.Build import cythonize
        
        sys.path.insert(0, str(Paths.PROJECT_ROOT))
        from ares.config import initialize, build_config, compiler_config
        initialize()
        
        # Get compiler directives using shared utility function
        compiler_directives = get_compiler_directives(build_config)
        
        inplace = build_config.get_bool("build", "inplace", True)
        compiler_flags = compiler_config.get_compiler_flags() or []
        
        # Filter compiler flags using shared utility function
        compiler_flags = filter_compiler_flags(compiler_flags)
        
        build_args = ['build_ext']
        if inplace:
            build_args.append('--inplace')
        
        # Get extensions to compile
        all_extensions = ExtManager.get_extensions(extra_compile_args=compiler_flags)
        
        # Check if modules already exist
        cython_dirs = Paths.get_cython_module_path()
        modules_already_exist = CModuleManager.check_modules_in_dirs(cython_dirs)
        
        # Force rebuilding if no modules exist
        if not modules_already_exist:
            log.info("No compiled modules found. Forcing compilation.")
            force = True
        
        # Check which files have changed and need rebuilding
        extensions_to_build = ExtManager.check_file_changes(all_extensions, force)
        
        if not extensions_to_build:
            log.info("No Cython files have changed. Skipping compilation.")
            return CModuleManager.check_compiled_modules(build_dir)
        
        log.info(f"Compiling {len(extensions_to_build)}/{len(all_extensions)} Cython modules...")
        
        # Create temp directory for the build
        if not build_dir.exists():
            os.makedirs(build_dir, exist_ok=True)
            
        # Run the build process
        old_argv = sys.argv.copy()
        try:
            status = cls._run_build_process(python_exe, extensions_to_build, compiler_directives, 
                                           build_args, build_log_path)
            if status != SUCCESS:
                log.error("Build process failed")
                return False
        finally:
            sys.argv = old_argv
        
        # Verify compiled modules
        return CModuleManager.check_compiled_modules(build_dir)
