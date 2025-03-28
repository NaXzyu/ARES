#!/usr/bin/env python3
"""Template management for PyInstaller spec files."""

import os
from pathlib import Path

# Get file and project directories
FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parent.parent
SPEC_DIR = PROJECT_ROOT / "ares" / "spec"
TEMPLATE_SPEC = SPEC_DIR / "executable.spec"

class SpecBuilder:
    """Builds PyInstaller spec files from templates."""
    
    def __init__(self, output_dir, main_script, name, resources_dir=None, console_mode=True, onefile=True):
        """Initialize the spec file builder."""
        self.output_dir = Path(output_dir) if output_dir else None
        self.main_script = Path(main_script) if main_script else None
        self.name = name
        self.resources_dir = Path(resources_dir) if resources_dir else None
        self.console_mode = console_mode
        self.onefile = onefile
        
        # Ensure output directory exists if provided
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
    
    def create_spec(self, binaries=None, hook_files=None):
        """Create a PyInstaller spec file from the template."""
        spec_file = self.output_dir / f"{self.name}.spec"
        
        if not TEMPLATE_SPEC.exists():
            print(f"Error: Template spec file not found at {TEMPLATE_SPEC}")
            print("Cannot continue without the template file.")
            return None
        
        try:
            with open(TEMPLATE_SPEC, 'r') as src, open(spec_file, 'w') as dst:
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
