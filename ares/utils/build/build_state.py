"""Build state tracking for incremental builds."""

import os
import json
import datetime
import hashlib
from pathlib import Path

from ares.utils import log
from ares.utils.build.build_utils import BuildUtils

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
    
    def should_rebuild(self, config):
        """Check if the build needs to be rebuilt.
        
        Args:
            config: Configuration to check for changes
            
        Returns:
            tuple: (rebuild_needed, reason)
        """
        if not self.state["last_build_time"]:
            return True, "No previous build exists"
            
        if not self.state_file.exists():
            return True, "No build state file exists"
            
        # Force a rebuild if config is None
        if config is None:
            return True, "No configuration provided"
        
        # Create a more robust function to sanitize all Path objects in the config
        def sanitize_paths(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: sanitize_paths(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [sanitize_paths(item) for item in obj]
            else:
                return obj
        
        # Apply our robust sanitizer to ensure no Path objects remain
        serializable_config = sanitize_paths(config)
        
        try:
            # Now it should be safe to serialize
            current_config = json.dumps(serializable_config, sort_keys=True)
            current_config_hash = hashlib.md5(current_config.encode()).hexdigest()
            
            if current_config_hash != self.state.get("config_hash"):
                return True, "Configuration has changed"
                
            return False, "No changes detected"
        except TypeError as e:
            # If serialization still fails, log the error and force a rebuild
            log.error(f"Error serializing configuration: {e}")
            return True, f"Configuration serialization error: {e}"

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
            # Compute and store config hash
            config_json = json.dumps(processed_config, sort_keys=True)
            self.state["config_hash"] = hashlib.md5(config_json.encode()).hexdigest()
        
        # Update file hashes:
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
                        file_hash = BuildUtils.compute_file_hash(file_path)
                        # Store the hash in the state
                        self.state["files"][str(rel_path)] = file_hash
                    except Exception as e:
                        log.warn(f"Error hashing file {file_path}: {e}")
        
        # Log the number of files tracked
        file_count = len(self.state["files"])
        log.info(f"Tracked {file_count} files for incremental build")
        
        # Save the updated state
        return self._save_state()
