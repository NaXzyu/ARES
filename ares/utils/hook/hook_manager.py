#!/usr/bin/env python3
"""Utility for managing PyInstaller runtime hooks for Ares Engine."""

import os
import shutil
from pathlib import Path

from ares.utils.log import log
from ares.utils.paths import Paths
from ares.utils.hook.hook_type import HookType

class HookManager:
    """Manager for PyInstaller hooks in Ares Engine."""
    
    # Define the correct hook execution order
    HOOK_EXECUTION_ORDER = [
        HookType.INIT_CONFIGS,    # Config system must be initialized first
        HookType.RUNTIME_LOGGING, # Logging system needs to be set up next
        HookType.ARES,            # Ares engine hook for common imports
        HookType.SDL2,            # SDL2 initialization
        HookType.CMODULES   # Cython modules loaded last
    ]
    
    @classmethod
    def get_hook_filename(cls, hook_type):
        """Get the filename for a hook type.
        
        Args:
            hook_type: HookType enum value
            
        Returns:
            str: Filename for the hook
        """
        return hook_type.value
    
    @classmethod
    def get_hook_pyinstaller_name(cls, hook_type):
        """Get the PyInstaller-compatible hook name.
        
        Args:
            hook_type: HookType enum value
            
        Returns:
            str: PyInstaller-compatible hook name
        """
        # Get the filename from the hook type
        filename = hook_type.value
        # Replace the '_hook.py' suffix with 'hook-<module_name>.py'
        module_name = filename.replace('_hook.py', '')
        return f"hook-{module_name}.py"
    
    @classmethod
    def get_runtime_hooks(cls, hooks_path=None):
        """Get a list of runtime hooks in the correct execution order.
        
        Args:
            hooks_path: Optional path where hook files are located
                      (defaults to ares/hooks directory)
                      
        Returns:
            list: List of paths to hook files in proper execution order
        """
        # Determine hooks directory path
        if hooks_path is None:
            try:
                # Get ares package path
                import ares
                ares_path = Path(ares.__file__).parent
                hooks_path = ares_path / "hooks"
            except ImportError:
                log.error("Error: Could not import ares package to find hooks directory")
                return []
        else:
            hooks_path = Path(hooks_path)
            
        # Check for all required hooks in the defined execution order
        runtime_hooks = []
        for hook_type in cls.HOOK_EXECUTION_ORDER:
            hook_path = hooks_path / cls.get_hook_filename(hook_type)
            if hook_path.exists():
                runtime_hooks.append(str(hook_path.resolve()))
            else:
                log.warning(f"Hook file not found: {hook_path}")
        
        return runtime_hooks
    
    @classmethod
    def verify_hooks(cls, hooks_path=None):
        """Verify that all required hooks are present.
        
        Args:
            hooks_path: Optional path where hook files are located
                      (defaults to ares/hooks directory)
                      
        Returns:
            tuple: (bool, list) - Success flag and list of missing hooks
        """
        # Determine hooks directory path
        if hooks_path is None:
            try:
                # Get ares package path
                import ares
                ares_path = Path(ares.__file__).parent
                hooks_path = ares_path / "hooks"
            except ImportError:
                log.error("Error: Could not import ares package to find hooks directory")
                return False, [hook_type for hook_type in HookType]
        else:
            hooks_path = Path(hooks_path)
        
        # Check for all required hooks
        missing_hooks = []
        for hook_type in HookType:
            hook_path = hooks_path / cls.get_hook_filename(hook_type)
            if not hook_path.exists():
                missing_hooks.append(hook_type)
        
        return len(missing_hooks) == 0, missing_hooks
    
    @classmethod
    def load_hook(cls, hooks_dir, source_hooks_dir, hook_type):
        """Load a specific hook from source directory to destination.
        
        Args:
            hooks_dir: Destination directory for created hooks
            source_hooks_dir: Source directory containing hook files
            hook_type: HookType enum value for the hook to load
            
        Returns:
            Path: Path to the created hook file, or None if not found
        """
        source_path = source_hooks_dir / cls.get_hook_filename(hook_type)
        
        if not source_path.exists():
            log.warn(f"Warning: Hook file {cls.get_hook_filename(hook_type)} not found in {source_hooks_dir}")
            return None
            
        # Create PyInstaller-compatible hook name
        dest_path = hooks_dir / cls.get_hook_pyinstaller_name(hook_type)
        
        try:
            shutil.copy2(source_path, dest_path)
            log.info(f"Created hook: {dest_path}")
            return dest_path
        except Exception as e:
            log.error(f"Error creating hook {cls.get_hook_pyinstaller_name(hook_type)}: {e}")
            return None

    @classmethod
    def create_runtime_hooks(cls, output_dir):
        """Create PyInstaller runtime hooks for Ares Engine in the correct order.
        
        Args:
            output_dir: Directory where hooks should be created
            
        Returns:
            list: List of paths to the created hook files in proper execution order
        """
        hooks_dir = Path(output_dir) / "hooks"
        os.makedirs(hooks_dir, exist_ok=True)
        
        hooks = []  # Use Paths API for hooks directory
        source_hooks_dir = Paths.get_hooks_path()
        
        # Load hooks in the defined execution order
        for hook_type in cls.HOOK_EXECUTION_ORDER:
            hook_path = cls.load_hook(hooks_dir, source_hooks_dir, hook_type)
            if hook_path:
                hooks.append(hook_path)
                log.info(f"Added hook {hook_type} for execution")
        
        log.info(f"Created {len(hooks)} hooks in proper execution order")
        return hooks

    @classmethod
    def create_basic_runtime_hooks(cls, output_dir):
        """Create only the essential PyInstaller runtime hooks for Ares Engine.
        
        This creates a minimal set of hooks for basic functionality.
        
        Args:
            output_dir: Directory where hooks should be created
            
        Returns:
            list: List of paths to the created hook files
        """
        hooks_dir = Path(output_dir) / "hooks"
        os.makedirs(hooks_dir, exist_ok=True)
        
        hooks = []

        # Use Paths API for hooks directory
        source_hooks_dir = Paths.get_hooks_path()
        
        # Load only the essential hooks for basic functionality
        basic_hook_types = [HookType.SDL2, HookType.CMODULES]
        
        for hook_type in basic_hook_types:
            hook_path = cls.load_hook(hooks_dir, source_hooks_dir, hook_type)
            if hook_path:
                hooks.append(hook_path)
                log.info(f"Added basic hook {hook_type} for execution")
        
        log.info(f"Created {len(hooks)} basic hooks for minimal functionality")
        return hooks
