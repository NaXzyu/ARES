#!/usr/bin/env python3
"""Template management for PyInstaller spec files."""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Union

from ares.utils.const import SPEC_EXTENSION, EXE_SPEC_TEMPLATE
from ares.utils.paths import Paths
from ares.utils.utils import verify_python

from .spec import Spec

class ExeSpec(Spec):
    """Builds PyInstaller spec files from templates."""
    
    def __init__(self, output_dir: Union[str, Path], main_script: Union[str, Path], 
                 name: str, resources_dir: Optional[Union[str, Path]] = None, 
                 console_mode: bool = True, onefile: bool = True):
        """Initialize the spec file builder.
        
        Args:
            output_dir: Directory where the spec file will be written
            main_script: Path to the main script for the executable
            name: Name of the executable
            resources_dir: Optional directory containing resources to include
            console_mode: Whether to show console window
            onefile: Whether to build a single-file executable
        """
        # Verify Python version before proceeding
        verify_python()
        
        super().__init__(output_dir, name)
        self.main_script = Path(main_script) if main_script else None
        self.resources_dir = Path(resources_dir) if resources_dir else None
        self.console_mode = console_mode
        self.onefile = onefile
        
        # Ensure output directory exists if provided
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
    
    def apply(self, binaries: Optional[List[Tuple[str, str]]] = None, 
                      hook_files: Optional[List[str]] = None) -> Optional[Path]:
        """Create a PyInstaller spec file from the template.
        
        Args:
            binaries: Optional list of (source, dest) tuples for binary files
            hook_files: Optional list of hook file paths
            
        Returns:
            Path to the created spec file if successful, None otherwise
        """
        # Use paths API for generating file paths and constants for extensions
        spec_file = Path(self.output_dir) / f"{self.name}{SPEC_EXTENSION}"
        template_spec = Paths.get_spec_template(EXE_SPEC_TEMPLATE)
        
        if not template_spec.exists():
            print(f"Error: Template spec file not found at {template_spec}")
            print("Cannot continue without the template file.")
            return None
        
        try:
            with open(template_spec, 'r') as src, open(spec_file, 'w') as dst:
                template = src.read()
                
                # Replace placeholders with actual values
                # Use Path.as_posix() to ensure consistent forward slashes in paths
                main_script_path = str(self.main_script.resolve().as_posix())
                template = template.replace("{{MAIN_SCRIPT}}", main_script_path)
                template = template.replace("{{NAME}}", self.name)
                
                # Use proper Python True/False values (capitalized)
                console_value = "True" if self.console_mode else "False"
                onefile_value = "True" if self.onefile else "False"
                template = template.replace("{{CONSOLE}}", console_value)
                template = template.replace("{{ONEFILE}}", onefile_value)
                
                if self.resources_dir and self.resources_dir.exists():
                    resources_path = str(self.resources_dir.resolve().as_posix())
                    resources_str = f"(r'{resources_path}', 'resources')"
                    template = template.replace("{{RESOURCES}}", resources_str)
                else:
                    template = template.replace("{{RESOURCES}}", "")
                    
                # Optional: Add binaries and hook files to template
                if binaries:
                    # Look for the right spot to inject binaries
                    binaries_marker = "    binaries=[],"
                    binaries_replacement = "    binaries=[\n"
                    for src, dest in binaries:
                        src_path = str(Path(src).resolve().as_posix())
                        binaries_replacement += f"        (r'{src_path}', r'{dest}'),\n"
                    binaries_replacement += "    ],"
                    template = template.replace(binaries_marker, binaries_replacement)
                
                # When adding hook files, ensure we handle both list and tuple
                if hook_files:
                    # Look for the right spot to inject runtime hooks
                    hooks_marker = "    runtime_hooks=[],"
                    hooks_replacement = "    runtime_hooks=[\n"
                    for hook in hook_files:
                        # Make sure hook exists before adding it
                        if hook and Path(hook).exists():
                            hook_path = str(Path(hook).resolve().as_posix())
                            hooks_replacement += f"        r'{hook_path}',\n"
                    hooks_replacement += "    ],"
                    template = template.replace(hooks_marker, hooks_replacement)
                
                dst.write(template)
                
            return spec_file
        except Exception as e:
            print(f"Error creating spec file from template: {e}")
            return None
