"""Build state tracking for incremental builds."""

import os
import json
import datetime
from pathlib import Path

from ares.utils import log
from ares.utils.build.utils import compute_file_hash

class BuildState:
    """Tracks build state for incremental builds."""
    
    def __init__(self, source_dir, build_dir, name=None):
        """Initialize build state tracker.
        
        Args:
            source_dir: Source directory to track
            build_dir: Build output directory
            name: Optional name for the build state file
        """
        self.source_dir = Path(source_dir)
        self.build_dir = Path(build_dir)
        self.name = name or self.source_dir.name
        
        # State file path - where we save build state
        self.state_file = self.build_dir / f"{self.name}.build_state.json"
        
        # Default empty state
        self.state = {
            "last_build_time": None,
            "config": {},
            "files": {}
        }
        
        # Try to load existing state
        self._load_state()
    
    def _load_state(self):
        """Load build state from file if it exists."""
        if not self.state_file.exists():
            log.info(f"No build state file found at {self.state_file}")
            return False
            
        try:
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
            log.info(f"Loaded build state from {self.state_file}")
            return True
        except (json.JSONDecodeError, OSError) as e:
            log.warn(f"Warning: Could not load build state: {e}")
            return False
    
    def _save_state(self):
        """Save current build state to file."""
        try:
            os.makedirs(self.state_file.parent, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            log.info(f"Saved build state to {self.state_file}")
            return True
        except OSError as e:
            log.warn(f"Warning: Could not save build state: {e}")
            return False
    
    def should_rebuild(self, config_override=None):
        """Check if project should be rebuilt."""
        # Case 1: No previous build
        if not self.state_file.exists() or not self.state["last_build_time"]:
            return True, "First build or missing state file"
        
        # Case 2: Executable not found
        exe_extension = ".exe" if os.name == "nt" else ""
        executable_path = self.build_dir / "out" / f"{self.name}{exe_extension}"
        
        if not executable_path.exists():
            return True, f"Executable not found: {executable_path}"
        
        # Case 3: Config changed
        if config_override:
            # Convert config_override to a JSON string for comparison
            from ares.utils.build.build_cache import _preprocess_paths_for_json
            
            # Preprocess paths in config_override to ensure consistent comparison
            processed_config = _preprocess_paths_for_json(config_override)
            current_config = json.dumps(processed_config, sort_keys=True)
            
            # Convert stored config to a JSON string for comparison
            stored_config = json.dumps(self.state["config"], sort_keys=True)
            
            if current_config != stored_config:
                return True, "Configuration changed"
        
        # Case 4: Source files changed
        extensions = ['.py', '.pyx', '.png', '.jpg', '.wav', '.mp3', '.json', '.tmx', '.tsx', '.ini']
        
        # Check for changes in tracked source files
        for ext in extensions:
            for file_path in self.source_dir.glob(f"**/*{ext}"):
                if file_path.is_file():
                    # Skip any .git directories
                    if ".git" in str(file_path):
                        continue
                        
                    try:
                        rel_path = file_path.relative_to(self.source_dir)
                        rel_path_str = str(rel_path)
                        file_hash = compute_file_hash(file_path)
                        
                        # Check if file is new or changed
                        if rel_path_str not in self.state["files"] or self.state["files"][rel_path_str] != file_hash:
                            return True, f"Source file changed: {rel_path}"
                    except Exception as e:
                        log.warn(f"Error checking file {file_path}: {e}")
                        # Skip this file for now
                        return True, f"Error checking file {file_path}"
        
        # No changes detected
        return False, "No changes detected"
    
    def mark_successful_build(self, config_override=None):
        """Mark a successful build, updating state.
        
        Args:
            config_override: Optional configuration to store
            
        Returns:
            bool: Whether state was successfully saved
        """
        # Update build time
        self.state["last_build_time"] = datetime.datetime.now().isoformat()
        
        # Process config override if provided
        if config_override:
            # Preprocess paths in config_override for JSON serialization
            processed_config = {}
            for key, value in config_override.items():
                if isinstance(value, Path):
                    processed_config[key] = str(value)
                elif isinstance(value, (list, tuple)):
                    if value and isinstance(value[0], (list, tuple)) and len(value[0]) == 2 and isinstance(value[0][0], Path):
                        processed_config[key] = [[str(path), desc] for path, desc in value]
                    else:
                        processed_config[key] = [str(item) if isinstance(item, Path) else item for item in value]
                elif isinstance(value, dict):
                    processed_config[key] = {k: str(v) if isinstance(v, Path) else v for k, v in value.items()}
                else:
                    processed_config[key] = value
            self.state["config"] = processed_config
        
        # Update file hashes
        tracked_extensions = ['.py', '.pyx', '.png', '.jpg', '.wav', '.mp3', '.json', '.tmx', '.tsx', '.ini']
        
        # Clear previous file hashes
        self.state["files"] = {}
        
        # Hash all tracked files
        for ext in tracked_extensions:
            for file_path in self.source_dir.glob(f"**/*{ext}"):
                if file_path.is_file():
                    # Skip any .git directories
                    if ".git" in str(file_path):
                        continue
                        
                    try:
                        rel_path = file_path.relative_to(self.source_dir)
                        file_hash = compute_file_hash(file_path)
                        # Store the hash in the state
                        self.state["files"][str(rel_path)] = file_hash
                    except Exception as e:
                        log.warn(f"Error hashing file {file_path}: {e}")
        
        # Log the number of files tracked
        file_count = len(self.state["files"])
        log.info(f"Tracked {file_count} files for incremental build")
        
        # Save the updated state
        return self._save_state()
