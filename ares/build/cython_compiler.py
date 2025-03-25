"""Module for compiling Cython extensions in the Ares Engine project."""

import os
import sys
import subprocess
from pathlib import Path

from ares.utils import log
from ares.utils.build_utils import get_cython_module_dirs, compute_file_hash
from ares.build.build_cache import load_build_cache, save_build_cache

def compile_cython_modules(python_exe, project_root, build_dir, build_log_path, force=False):
    """Compile the Cython modules for the project.
    
    Args:
        python_exe: Path to Python executable
        project_root: Path to project root
        build_dir: Path to build directory
        build_log_path: Path to build log file
        force: Whether to force rebuilding all modules
        
    Returns:
        bool: True if compilation succeeded, False otherwise
    """
    from setuptools import setup
    from Cython.Build import cythonize
    
    sys.path.insert(0, str(project_root))
    from ares.config import initialize, build_config
    initialize()
    
    compiler_directives = {
        'language_level': build_config.getint("cython", "language_level", 3),
        'boundscheck': build_config.getboolean("cython", "boundscheck", False),
        'wraparound': build_config.getboolean("cython", "wraparound", False),
        'cdivision': build_config.getboolean("cython", "cdivision", True),
    }
    
    optimization = build_config.get("compiler", "optimization_level", "O2")
    inplace = build_config.getboolean("build", "inplace", True)
    
    old_argv = sys.argv.copy()
    
    if os.name == 'nt':
        if optimization == "O0":
            opt_flag = "/Od"
        elif optimization == "O1":
            opt_flag = "/O1"
        elif optimization == "O3":
            opt_flag = "/Ox"
        else:
            opt_flag = "/O2"
    else:
        opt_flag = f"-{optimization}"
    
    build_args = ['build_ext']
    if inplace:
        build_args.append('--inplace')
    
    all_extensions = get_extensions(project_root, extra_compile_args=[opt_flag])
    
    extensions_to_build = check_file_changes(all_extensions, project_root, build_dir, force)
    
    if not extensions_to_build:
        log.info("No Cython files have changed. Skipping compilation.")
        return check_compiled_modules(project_root, build_dir)
    
    log.info(f"Compiling {len(extensions_to_build)}/{len(all_extensions)} Cython modules...")
    
    if not build_dir.exists():
        os.makedirs(build_dir, exist_ok=True)
    temp_setup = build_dir / "temp_setup.py"
    
    try:
        with open(temp_setup, "w") as f:
            f.write("""
from setuptools import setup
from Cython.Build import cythonize
import sys
from setuptools.extension import Extension

ext_modules = []
""")
            for i, ext in enumerate(extensions_to_build):
                f.write(f"""
ext_{i} = Extension(
    "{ext.name}", 
    {ext.sources},
    extra_compile_args={ext.extra_compile_args if hasattr(ext, 'extra_compile_args') else None}
)
ext_modules.append(ext_{i})
""")
            
            f.write(f"""
setup(
    name="ares_cython_modules",
    ext_modules=cythonize(
        ext_modules,
        compiler_directives={compiler_directives}
    )
)
""")
        
        if extensions_to_build:
            run_cmd = [str(python_exe), str(temp_setup)]
            run_cmd.extend(build_args)
            
            # Capture Cython compiler output
            process = subprocess.Popen(
                run_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )
            
            # Log Cython compilation output to build log
            with open(build_log_path, 'a') as log_file:
                log_file.write("\n--- Cython Compilation Output ---\n")
                for line in process.stdout:
                    log_file.write(line)
                    # Only print summary info to console
                    if "Cythonizing" in line or "warning" in line.lower() or "error" in line.lower():
                        print(line.strip())
            
            # Wait for process to complete
            ret_code = process.wait()
            if ret_code != 0:
                log.error(f"Cython compilation failed with return code {ret_code}")
            
            cache = load_build_cache()
            cache["rebuilt_modules"] = True
            save_build_cache(cache)
        
    finally:
        if temp_setup.exists():
            os.unlink(temp_setup)
        sys.argv = old_argv
    
    return check_compiled_modules(project_root, build_dir)

def check_compiled_modules(project_root, build_dir):
    """Check if the Cython modules are compiled and move them if needed."""
    log.info("Checking for compiled modules...")
    
    # Get Cython directories using the centralized function
    cython_dirs = get_cython_module_dirs(project_root, error_on_missing=True)
    
    if not cython_dirs:
        log.error("Error: No Cython module directories defined in project.ini.")
        log.error("Please define module_dirs in the [cython] section of project.ini.")
        sys.exit(1)
    
    modules_found = False
    
    for cython_dir, desc in cython_dirs:
        for ext in ['.pyd', '.so']:
            if list(cython_dir.glob(f"*{ext}")):
                modules_found = True
                log.info(f"Found compiled {desc}")
                break
    
    if not modules_found:
        build_dirs = [d for d in build_dir.glob("lib.*")]
        if build_dirs:
            for cython_dir, desc in cython_dirs:
                module_name = cython_dir.name
                source_path = build_dirs[0] / "ares" / module_name
                if source_path.exists():
                    for ext in ['.pyd', '.so']:
                        for file in source_path.glob(f"*{ext}"):
                            target = cython_dir / file.name
                            log.info(f"Moving {file} to {target}")
                            try:
                                os.makedirs(cython_dir, exist_ok=True)
                                import shutil
                                shutil.copy2(file, target)
                                modules_found = True
                            except Exception as e:
                                log.error(f"Error copying file {file} to {target}: {e}")
    
    if modules_found:
        log.info("Cython modules compiled successfully.")
    else:
        log.error("Error: Could not find compiled Cython modules.")
        sys.exit(1)
        
    return modules_found

def get_extensions(project_root, extra_compile_args=None):
    """Define Cython extension modules for compilation."""
    from setuptools.extension import Extension
    
    if extra_compile_args is None:
        extra_compile_args = []
        
    extensions = []
    
    # Get extensions from package.ini
    sys.path.insert(0, str(project_root))
    from ares.config import config
    package_config = config.load("package")
    
    if package_config and package_config.has_section("extensions"):
        for name, path_spec in package_config.items("extensions"):
            if ":" not in path_spec:
                log.error(f"Error: Invalid extension format for {name}: {path_spec}")
                log.error("Extension format should be 'module.name:path/to/file.pyx'")
                sys.exit(1)
                
            module_name, pyx_path = path_spec.split(":", 1)
            pyx_path = pyx_path.strip()
            
            if not Path(pyx_path).exists():
                log.error(f"Error: Extension source file not found: {pyx_path}")
                log.error("Please verify the path is correct in package.ini")
                sys.exit(1)
                
            extensions.append(
                Extension(
                    module_name,
                    [pyx_path],
                    extra_compile_args=extra_compile_args
                )
            )
    
    # Report error if no extensions defined
    if not extensions:
        log.error("Error: No Cython extensions defined in package.ini")
        log.error("Please add extension definitions to the [extensions] section")
        log.error("Format: name = module.name:path/to/file.pyx")
        sys.exit(1)
    
    return extensions

def check_file_changes(extensions, project_root, build_dir, force=False):
    """Check which files have changed since the last build."""
    if force:
        log.info("Force rebuild requested, rebuilding all Cython modules.")
        return extensions
        
    cache = load_build_cache()
    changed_extensions = []
    
    for ext in extensions:
        ext_changed = False
        for source in ext.sources:
            source_path = Path(source)
            if not source_path.exists():
                log.warn(f"Warning: Source file {source} not found.")
                ext_changed = True
                continue
                
            current_hash = compute_file_hash(source_path)
            cached_hash = cache["files"].get(str(source_path), None)
            
            if cached_hash != current_hash:
                log.info(f"File {source_path.name} has changed or is new.")
                cache["files"][str(source_path)] = current_hash
                ext_changed = True
                
            pxd_path = source_path.with_suffix('.pxd')
            if pxd_path.exists():
                current_hash = compute_file_hash(pxd_path)
                cached_hash = cache["files"].get(str(pxd_path), None)
                
                if cached_hash != current_hash:
                    log.info(f"File {pxd_path.name} has changed.")
                    cache["files"][str(pxd_path)] = current_hash
                    for ext_obj in extensions:
                        if str(source_path) in ext_obj.sources:
                            if ext_obj not in changed_extensions:
                                changed_extensions.append(ext_obj)
    
        if ext_changed:
            changed_extensions.append(ext)
    
    import datetime
    cache["last_build"] = datetime.datetime.now().isoformat()
    save_build_cache(cache)
    
    return changed_extensions
