#!/usr/bin/env python3
"""Template management for PyInstaller spec files."""

import os
from pathlib import Path

# Get file and project directories
FILE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FILE_DIR.parent.parent

def create_spec_file(
    output_dir, 
    main_script, 
    name, 
    binaries, 
    hook_files, 
    resources_dir=None, 
    console_mode=True,
    onefile=True
):
    """Create a PyInstaller spec file for the build."""
    # Always use the template approach
    return create_spec_from_template(
        output_dir,
        main_script,
        name,
        resources_dir,
        console_mode,
        onefile,
        binaries=binaries,
        hook_files=hook_files
    )

def escape_windows_path(path_str):
    """Properly escape Windows paths to avoid Unicode escape issues."""
    # Replace single backslashes with double backslashes
    return path_str.replace('\\', '\\\\')

def create_spec_from_template(
    output_dir,
    main_script,
    name,
    resources_dir=None,
    console_mode=True,
    onefile=True,
    binaries=None,
    hook_files=None
):
    """Create a PyInstaller spec file from the template."""
    spec_file = Path(output_dir) / f"{name}.spec"
    template_spec = FILE_DIR / "template.spec"
    
    if not template_spec.exists():
        print(f"Error: Template spec file not found at {template_spec}")
        print("Cannot continue without the template file.")
        return None
    
    try:
        with open(template_spec, 'r') as src, open(spec_file, 'w') as dst:
            template = src.read()
            
            # Replace placeholders with actual values
            # Convert to raw string format for Python paths to avoid escape issues
            main_script_path = escape_windows_path(os.path.normpath(str(Path(main_script).resolve())))
            template = template.replace("{{MAIN_SCRIPT}}", main_script_path)
            template = template.replace("{{NAME}}", name)
            
            # Use proper Python True/False values (capitalized)
            console_value = "True" if console_mode else "False"
            onefile_value = "True" if onefile else "False"
            template = template.replace("{{CONSOLE}}", console_value)
            template = template.replace("{{ONEFILE}}", onefile_value)
            
            if resources_dir and Path(resources_dir).exists():
                resources_path = escape_windows_path(os.path.normpath(str(resources_dir)))
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
                    src_path = escape_windows_path(os.path.normpath(str(src)))
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
                        hook_path = escape_windows_path(os.path.normpath(str(hook)))
                        hooks_replacement += f"        r'{hook_path}',\n"
                hooks_replacement += "    ],"
                template = template.replace(hooks_marker, hooks_replacement)
            
            dst.write(template)
            
        return spec_file
    except Exception as e:
        print(f"Error creating spec file from template: {e}")
        return None
