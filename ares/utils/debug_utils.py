"""Debugging utilities for Ares Engine."""

import os
import sys
import logging

def dump_module_search_paths(logger=None):
    """Logs Python module search paths to help debugging import issues."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.debug("Python module search paths:")
    for i, path in enumerate(sys.path):
        logger.debug(f"  {i}: {path}")
    
    # Check if running in frozen environment
    if getattr(sys, 'frozen', False):
        meipass_path = sys._MEIPASS
        logger.debug(f"PyInstaller bundle contents at {meipass_path}:")
        
        try:
            # List top-level directories in MEIPASS
            for item in os.listdir(meipass_path):
                item_path = os.path.join(meipass_path, item)
                if os.path.isdir(item_path):
                    logger.debug(f"  Directory: {item}")
                else:
                    logger.debug(f"  File: {item}")
        except Exception as e:
            logger.error(f"Error listing bundle contents: {e}")

def inspect_module_loading(module_name, logger=None):
    """Attempts to import a module and logs detailed information about the process."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.debug(f"Attempting to import module: {module_name}")
    
    try:
        # Try direct import first
        logger.debug(f"Trying direct import of {module_name}")
        module = __import__(module_name)
        logger.debug(f"Successfully imported {module_name}")
        logger.debug(f"Module location: {getattr(module, '__file__', 'unknown')}")
        return module
    except ImportError as e:
        logger.debug(f"Direct import failed: {e}")
        
        # Try importlib
        try:
            import importlib
            logger.debug(f"Trying importlib.import_module({module_name})")
            module = importlib.import_module(module_name)
            logger.debug(f"importlib succeeded for {module_name}")
            logger.debug(f"Module location: {getattr(module, '__file__', 'unknown')}")
            return module
        except ImportError as e:
            logger.debug(f"importlib import failed: {e}")
            
            # Try spec-based import
            try:
                import importlib.util
                logger.debug("Looking for module spec...")
                
                # Check all paths in sys.path
                for path in sys.path:
                    potential_paths = []
                    
                    # For regular modules
                    potential_paths.append(os.path.join(path, module_name + '.py'))
                    
                    # For packages
                    potential_paths.append(os.path.join(path, module_name, '__init__.py'))
                    
                    # For compiled extensions
                    if os.name == 'nt':
                        potential_paths.append(os.path.join(path, module_name + '.pyd'))
                    else:
                        potential_paths.append(os.path.join(path, module_name + '.so'))
                    
                    for potential_path in potential_paths:
                        if os.path.exists(potential_path):
                            logger.debug(f"Found potential module at: {potential_path}")
                
                logger.debug("Module not found in any sys.path location")
                return None
            except Exception as inner_e:
                logger.debug(f"Error during spec search: {inner_e}")
                return None

def diagnose_imports(module_names, logger=None):
    """Diagnoses import issues for multiple modules."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.debug("=== Import Diagnostics ===")
    dump_module_search_paths(logger)
    
    for module_name in module_names:
        logger.debug(f"\n--- Diagnosing: {module_name} ---")
        inspect_module_loading(module_name, logger)
