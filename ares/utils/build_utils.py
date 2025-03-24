"""
Build utility functions for Ares Engine.
"""
from pathlib import Path

def find_main_script(directory):
    """Find a Python script with an entry point in the directory.
    
    Searches for a file with "if __name__ == '__main__':" to use as the entry point.
    Falls back to main.py if it exists.
    
    Args:
        directory: Path to search for Python scripts
        
    Returns:
        Path to the main script or None if not found
    """
    directory = Path(directory)
    
    # First, check for main.py as a convention
    main_script = directory / "main.py"
    if main_script.exists():
        return main_script
    
    # Look for Python files with entry points
    entry_point_files = []
    for py_file in directory.glob("**/*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "if __name__ == '__main__':" in content or 'if __name__ == "__main__":' in content:
                    entry_point_files.append(py_file)
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    # Use the first entry point file found
    if entry_point_files:
        # Prefer entry points in the root directory
        root_entry_points = [f for f in entry_point_files if f.parent == directory]
        if root_entry_points:
            return root_entry_points[0]
        return entry_point_files[0]
    
    return None
