#!/usr/bin/env python3
"""
Build script for Ares Engine package and executable.
"""

import os
import sys
import subprocess
import shutil
import time
import datetime
import argparse
from pathlib import Path

# Calculate paths directly in this file instead of importing from constants
FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parent.parent
BUILD_DIR = PROJECT_ROOT / "build"

sys.path.insert(0, str(PROJECT_ROOT))

# Import only the utility functions needed
from ares.utils.utils import format_size, format_time

def check_compiled_modules():
    """Check if the Cython modules are compiled and move them if needed."""
    print("Checking for compiled modules...")
    
    # Define directories to check for compiled modules
    cython_dirs = [
        (PROJECT_ROOT / "ares" / "math", "math modules"),
        (PROJECT_ROOT / "ares" / "physics", "physics modules"),
        (PROJECT_ROOT / "ares" / "renderer", "renderer modules")
    ]
    
    modules_found = False
    
    # First check if modules exist in their own directories
    for cython_dir, desc in cython_dirs:
        for ext in ['.pyd', '.so']:
            if list(cython_dir.glob(f"*{ext}")):
                modules_found = True
                print(f"Found compiled {desc}")
                break
    
    # If not found, look in build directory and copy them to the package directories
    if not modules_found:
        build_dirs = [d for d in BUILD_DIR.glob("lib.*")]
        if build_dirs:
            for cython_dir, desc in cython_dirs:
                module_name = cython_dir.name
                source_path = build_dirs[0] / "ares" / module_name
                if source_path.exists():
                    for ext in ['.pyd', '.so']:
                        for file in source_path.glob(f"*{ext}"):
                            target = cython_dir / file.name
                            print(f"Moving {file} to {target}")
                            shutil.copy2(file, target)
                            modules_found = True
    
    if modules_found:
        print("Cython modules compiled successfully.")
    else:
        print("Error: Could not find compiled Cython modules.")
        sys.exit(1)
        
    return modules_found

def get_extensions(extra_compile_args=None):
    """Define Cython extension modules for compilation."""
    from setuptools.extension import Extension
    
    if extra_compile_args is None:
        extra_compile_args = []
    
    # Define all extension modules here in one place
    extensions = [
        Extension(
            "ares.math.vector", 
            ["ares/math/vector.pyx"],
            extra_compile_args=extra_compile_args
        ),
        Extension(
            "ares.math.matrix", 
            ["ares/math/matrix.pyx"],
            extra_compile_args=extra_compile_args
        ),
        Extension(
            "ares.physics.collision", 
            ["ares/physics/collision.pyx"],
            extra_compile_args=extra_compile_args
        )
    ]
    
    return extensions

def compile_cython_modules(python_exe):
    """Compile the Cython modules for the project."""
    from setuptools import setup
    from Cython.Build import cythonize
    
    # Load configuration - fail if not available
    sys.path.insert(0, str(PROJECT_ROOT))
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
    
    # Set optimization flags based on platform
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
    
    # Set build_ext arguments
    build_args = ['build_ext']
    if inplace:
        build_args.append('--inplace')
    
    # Get extension modules with optimization flags
    extensions = get_extensions(extra_compile_args=[opt_flag])
    
    # Print what we're doing
    print("Compiling Cython modules...")
    
    # Create a temporary setup.py file for compiling
    if not BUILD_DIR.exists():
        os.makedirs(BUILD_DIR, exist_ok=True)
    temp_setup = BUILD_DIR / "temp_setup.py"
    
    try:
        with open(temp_setup, "w") as f:
            f.write("""
from setuptools import setup
from Cython.Build import cythonize
import sys
from setuptools.extension import Extension

ext_modules = []
""")
            # Add each extension
            for i, ext in enumerate(extensions):
                f.write(f"""
ext_{i} = Extension(
    "{ext.name}", 
    {ext.sources},
    extra_compile_args={ext.extra_compile_args if hasattr(ext, 'extra_compile_args') else None}
)
ext_modules.append(ext_{i})
""")
            
            # Write setup call
            f.write(f"""
setup(
    name="ares_cython_modules",
    ext_modules=cythonize(
        ext_modules,
        compiler_directives={compiler_directives}
    )
)
""")
        
        # Run the setup
        run_cmd = [str(python_exe), str(temp_setup)]
        run_cmd.extend(build_args)
        subprocess.check_call(run_cmd)
        
    finally:
        # Clean up the temporary file
        if temp_setup.exists():
            os.unlink(temp_setup)
        sys.argv = old_argv
    
    # Check if modules were compiled successfully
    return check_compiled_modules()

def build_engine(python_exe):
    """Build the Ares Engine package.
    
    Args:
        python_exe: Path to the Python executable to use for building
    """
    print(f"Using Python: {python_exe}")
    
    build_start = datetime.datetime.now()
    build_start_time = time.time()
    
    # Load configuration - fail if not available
    sys.path.insert(0, str(PROJECT_ROOT))
    from ares.config import initialize, build_config, config
    initialize()
    print("Loaded build configuration")
    
    pkg_data_config = config.load("pkg_data")
    print("Loaded package data configuration")
    
    # Create build directory if needed
    if not BUILD_DIR.exists():
        os.makedirs(BUILD_DIR, exist_ok=True)
    
    # Create build log file
    build_log_path = BUILD_DIR / "build_log.txt"
    
    with open(build_log_path, "a") as log:
        log.write(f"\n\n--- Build started at {build_start.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    
    # Compile Cython modules first
    print("Compiling Cython modules...")
    if not compile_cython_modules(python_exe):
        print("Error: Failed to compile Cython modules.")
        sys.exit(1)
    
    print("Compilation complete. Building packages...")
    
    # Build wheel package
    print("\nBuilding wheel package...")
    wheel_start_time = time.time()
    wheel_cmd = [str(python_exe), "-m", "pip", "wheel", ".", "-w", str(BUILD_DIR)]
    try:
        subprocess.run(wheel_cmd, check=True)
        
        wheel_files = list(BUILD_DIR.glob("*.whl"))
        if wheel_files:
            wheel_file = wheel_files[0]
            wheel_size = os.path.getsize(wheel_file)
            print(f"Created wheel package: {wheel_file}")
            print(f"Size: {format_size(wheel_size)}")
        else:
            print("Error: Wheel file not found after build.")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error building wheel: {e}")
        sys.exit(1)
    
    # Build source distribution
    print("\nBuilding source distribution...")
    sdist_cmd = [str(python_exe), "setup.py", "sdist", "--dist-dir", str(BUILD_DIR)]
    try:
        subprocess.run(sdist_cmd, check=True)
        
        sdist_files = list(BUILD_DIR.glob("*.tar.gz"))
        if sdist_files:
            sdist_file = sdist_files[0]
            sdist_size = os.path.getsize(sdist_file)
            print(f"Created source distribution: {sdist_file}")
            print(f"Size: {format_size(sdist_size)}")
        else:
            print("Error: Source distribution not found after build.")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error building source distribution: {e}")
        sys.exit(1)
    
    # Calculate build duration
    build_end_time = time.time()
    build_duration = build_end_time - build_start_time
    
    # Write build log
    with open(build_log_path, "a") as log:
        log.write(f"Build completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Build duration: {format_time(build_duration)}\n")
        log.write("Build artifacts:\n")
        wheel_files = list(BUILD_DIR.glob("*.whl"))
        sdist_files = list(BUILD_DIR.glob("*.tar.gz"))
        for file in wheel_files + sdist_files:
            log.write(f"  - {file.name} ({format_size(os.path.getsize(file))})\n")
    
    # Print build summary
    print("\n" + "="*50)
    print(" BUILD SUMMARY ".center(50, "="))
    print("="*50)
    print(f"Build time:      {format_time(build_duration)}")
    print(f"Build log:       {build_log_path}")
    print("Build artifacts:")
    for file in wheel_files + sdist_files:
        print(f"  - {file.name} ({format_size(os.path.getsize(file))})")
    print("="*50 + "\n")
    
    print(f"\nBuild completed successfully. Packages available in: {BUILD_DIR}")
    print("\nTo install the engine, run:")
    wheel_file = wheel_files[0].name if wheel_files else "*.whl"
    print(f"pip install {BUILD_DIR / wheel_file}")
    
    return True

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Build the Ares Engine.")
    parser.add_argument('--python', required=True,
                        help='Path to the Python executable to use for building')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    build_engine(args.python)
