"""Module for tracking build state and enabling incremental builds."""

import os
import json
import time
from pathlib import Path

from ares.utils import log
from ares.utils.build_utils import compute_file_hash, hash_config

class BuildState:
    """Tracks the state of a build to enable incremental builds."""
    
    def __init__(self, project_dir, output_dir, name="project"):
        """Initialize build state tracker.
        
        Args:
            project_dir: Source directory of the project
            output_dir: Directory where build outputs are stored
            name: Name of the project (used in state file naming)
        """
        self.project_dir = Path(project_dir)
        self.output_dir = Path(output_dir)
        self.name = name
        
        # State file location in the output directory
        self.state_file = self.output_dir / f".build_state_{name}.json"
        
        # Current state
        self.state = {
            "last_build_time": 0,
            "file_hashes": {},
            "build_config_hash": "",
            "dependencies": {}
        }
        
        # Load existing state if available
        self._load_state()
    
    def _load_state(self):
        """Load build state from state file if it exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
                log.info(f"Loaded build state from {self.state_file}")
            except (json.JSONDecodeError, IOError) as e:
                log.warn(f"Failed to load build state: {e}")
    
    def save_state(self):
        """Save current build state to the state file."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            log.info(f"Saved build state to {self.state_file}")
            return True
        except IOError as e:
            log.error(f"Failed to save build state: {e}")
            return False
    
    def update_file_hashes(self):
        """Update hashes for all relevant files in the project."""
        new_hashes = {}
        
        # Process Python files and other source files
        for pattern in ["**/*.py", "**/*.pyx", "**/*.pxd", "**/*.c", "**/*.h"]:
            for file_path in self.project_dir.glob(pattern):
                if file_path.is_file():
                    rel_path = file_path.relative_to(self.project_dir)
                    file_hash = compute_file_hash(file_path)
                    if file_hash:  # Only add if hash was computed successfully
                        new_hashes[str(rel_path)] = file_hash
        
        self.state["file_hashes"] = new_hashes
        self.state["last_build_time"] = time.time()
    
    def should_rebuild(self, config=None):
        """Determine if a rebuild is necessary based on file or config changes.
        
        Args:
            config: Current build configuration to compare with previous build
            
        Returns:
            tuple: (rebuild_needed, reason)
        """
        # First build or no state file
        if not self.state_file.exists():
            return True, "First build or missing state file"
        
        # Check if build configuration has changed
        if config:
            current_config_hash = hash_config(config)
            previous_config_hash = self.state.get("build_config_hash", "")
            if current_config_hash != previous_config_hash:
                return True, "Build configuration has changed"
        
        # Check for new or modified files
        previous_hashes = self.state.get("file_hashes", {})
        for pattern in ["**/*.py", "**/*.pyx", "**/*.pxd", "**/*.c", "**/*.h"]:
            for file_path in self.project_dir.glob(pattern):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(self.project_dir))
                    current_hash = compute_file_hash(file_path)
                    if (rel_path not in previous_hashes or
                            previous_hashes[rel_path] != current_hash):
                        return True, f"File changed: {rel_path}"
        
        # Check for deleted files
        current_files = set()
        for pattern in ["**/*.py", "**/*.pyx", "**/*.pxd", "**/*.c", "**/*.h"]:
            for file_path in self.project_dir.glob(pattern):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(self.project_dir))
                    current_files.add(rel_path)
        
        for rel_path in previous_hashes.keys():
            if rel_path not in current_files:
                return True, f"File removed: {rel_path}"
        
        # Check if the executable exists
        executable_ext = '.exe' if os.name == 'nt' else ''
        executable = self.output_dir / f"{self.name}{executable_ext}"
        if not executable.exists():
            return True, f"Executable not found: {executable}"
        
        return False, "No changes detected"
    
    def mark_successful_build(self, config=None):
        """Mark the current build as successful and update state."""
        self.update_file_hashes()
        if config:
            self.state["build_config_hash"] = hash_config(config)
        self.save_state()
