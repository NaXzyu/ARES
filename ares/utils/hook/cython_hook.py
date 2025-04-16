"""Cython modules hook - enables dynamic loading of extension modules"""

import os
import sys
import traceback
import importlib.util
import importlib.machinery
import types

from ares.utils.const import (
    PYD_EXTENSION,
    SO_EXTENSION
)

def ensure_directory_exists(path):
    """Creates directory if missing"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def create_init_file(directory):
    """Generates __init__.py for package structure"""
    init_file = os.path.join(directory, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Auto-generated __init__.py file for PyInstaller\n')
    return init_file

def load_binary_module(name, path):
    """Loads extension modules directly from frozen path"""
    try:
        # Fix: Extract the actual module name without extensions or python version tags
        # Original module name format: vector.cp312-win_amd64.pyd
        # We need just: vector
        base_name = os.path.basename(path)
        simple_name = base_name.split('.')[0]  # Get just 'vector' part
        # Use correct naming: name.simple_name for full module path
        package_name = name.rsplit('.', 1)[0] if '.' in name else name
        full_module_name = f"{package_name}.{simple_name}"
        
        print(f"Ares Engine: Loading module {simple_name} from {path}")
        
        # Use a simpler approach for loading extension modules
        # This avoids issues with method assignments on immutable types
        spec = importlib.machinery.ExtensionFileLoader(full_module_name, path).create_module(None)
        if spec:
            # Register the module before loading to avoid circular import issues
            sys.modules[full_module_name] = spec
            loader = importlib.machinery.ExtensionFileLoader(full_module_name, path)
            loader.exec_module(spec)
            print(f"Ares Engine: Successfully loaded {full_module_name}")
            return spec
    except Exception as e:
        print(f"Ares Engine: Error loading {name} from {path}: {e}")
        import traceback
        traceback.print_exc()
    return None

# Setup package structure in frozen application
if getattr(sys, 'frozen', False):
    # We're running in a PyInstaller bundle
    root_path = sys._MEIPASS
    
    # Make sure ares package exists
    if 'ares' not in sys.modules:
        ares_module = types.ModuleType('ares')
        sys.modules['ares'] = ares_module
        ares_module.__path__ = [os.path.join(root_path, 'ares')]
        # Create package directory
        ensure_directory_exists(os.path.join(root_path, 'ares'))
        # Create __init__.py
        create_init_file(os.path.join(root_path, 'ares'))
    
    # Load core modules first
    if not hasattr(sys.modules['ares'], 'core'):
        core_module = types.ModuleType('ares.core')
        sys.modules['ares.core'] = core_module
        core_dir = os.path.join(root_path, 'ares', 'core')
        if not os.path.exists(core_dir):
            os.makedirs(core_dir, exist_ok=True)
        core_module.__path__ = [core_dir]
        create_init_file(core_dir)
        
        # Explicitly import core Window and Input classes
        print("Ares Engine: Setting up core modules...")
        try:
            from importlib.machinery import SourceFileLoader
            window_path = os.path.join(core_dir, 'window.py')
            input_path = os.path.join(core_dir, 'input.py')
            
            if os.path.exists(window_path):
                window_module = SourceFileLoader('ares.core.window', window_path).load_module()
                sys.modules['ares.core.window'] = window_module
                # Add Window class to ares module for direct access
                if hasattr(window_module, 'Window'):
                    sys.modules['ares'].__dict__['Window'] = window_module.Window
                    print("Ares Engine: Window class registered")
            
            if os.path.exists(input_path):
                input_module = SourceFileLoader('ares.core.input', input_path).load_module()
                sys.modules['ares.core.input'] = input_module
                # Add Input class to ares module for direct access
                if hasattr(input_module, 'Input'):
                    sys.modules['ares'].__dict__['Input'] = input_module.Input
                    print("Ares Engine: Input class registered")
                    
        except Exception as e:
            print(f"Ares Engine: Error setting up core modules: {e}")
            traceback.print_exc()
    
    # Load all Cython modules for key Ares Engine components
    # Order matters - load vector first, then matrix, then physics
    module_load_order = [
        ('math', ['vector', 'matrix']),  # Load vector before matrix
        ('physics', ['collision']),
        ('renderer', []),
        ('core', [])
    ]
    extensions = [PYD_EXTENSION, SO_EXTENSION]
    
    for dir_name, priority_modules in module_load_order:
        module_dir = os.path.join(root_path, 'ares', dir_name)
        if os.path.exists(module_dir):
            print(f"Ares Engine: Found module directory: {module_dir}")
            
            # Ensure the package exists
            package_name = f'ares.{dir_name}'
            if package_name not in sys.modules:
                package = types.ModuleType(package_name)
                sys.modules[package_name] = package
                package.__path__ = [module_dir]
                
            # Create __init__.py
            create_init_file(module_dir)
            
            # First load priority modules in the specified order
            for module_name in priority_modules:
                for ext in extensions:
                    module_path = os.path.join(module_dir, f"{module_name}{ext}")
                    if os.path.exists(module_path):
                        load_binary_module(package_name, module_path)
                        break
            
            # Then load any remaining modules
            for ext in extensions:
                for module_file in os.listdir(module_dir):
                    if module_file.endswith(ext):
                        module_base = os.path.splitext(module_file)[0].split('.')[0]
                        if module_base not in priority_modules:
                            module_path = os.path.join(module_dir, module_file)
                            load_binary_module(package_name, module_path)
