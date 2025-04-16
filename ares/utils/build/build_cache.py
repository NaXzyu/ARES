"""Build cache for tracking file changes during build process."""
import datetime
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict

from ares.utils.log import log
from ares.utils.paths import Paths

# Add this module-level function to allow direct import
def _preprocess_paths_for_json(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Path objects to strings for JSON serialization.
    
    Args:
        config: Configuration dictionary that may contain Path objects
        
    Returns:
        Dict with Path objects converted to strings
    """
    # Get the singleton instance of BuildCache
    instance = BuildCache.get_instance()
    # Call the instance method to do the actual processing
    return instance._preprocess_paths_for_json(config)

class BuildCache:
    """Cache for storing file hashes and other build state information."""
    
    # Class variables for singleton pattern
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        """Initialize build cache with empty data."""
        self.cache = {
            "last_build": None,
            "files": {},
            "rebuild_flag": False
        }
        self.cache_file = None
        self.dirty = False
        
    @classmethod
    def get_instance(cls) -> 'BuildCache':
        """Get the singleton instance of BuildCache."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    cls._instance.cache_file = Paths.get_build_cache_file()
                    cls._instance.load()
        return cls._instance
    
    @classmethod
    def set_cache_paths(cls, output_dir: Path) -> tuple:
        """Set up cache paths based on output directory.
        
        Args:
            output_dir: Directory to place the cache file in
            
        Returns:
            tuple: (cache_dir, cache_file) paths
        """
        if not output_dir:
            cache_dir = Paths.get_cache_path()
        else:
            cache_dir = output_dir / "cache"
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Define cache file path
        cache_file = cache_dir / "build_cache.json"
        
        # Update the instance if it exists
        if cls._instance is not None:
            cls._instance.cache_file = cache_file
        
        return cache_dir, cache_file
    
    def load(self) -> Dict:
        """Load cache from file if it exists.
        
        Returns:
            dict: Loaded cache data or empty cache
        """
        if not self.cache_file or not os.path.exists(self.cache_file):
            return self.cache
        
        try:
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
            self.dirty = False
        except (json.JSONDecodeError, OSError) as e:
            log.warn(f"Error loading build cache: {e}")
            # Initialize with empty cache
            self.cache = {
                "last_build": None,
                "files": {},
                "rebuild_flag": False
            }
            self.dirty = True
            
        # Initialize the rebuild flag if it doesn't exist
        if "rebuild_flag" not in self.cache:
            self.cache["rebuild_flag"] = False
            self.dirty = True
            
        # Initialize the files dict if it doesn't exist
        if "files" not in self.cache:
            self.cache["files"] = {}
            self.dirty = True
            
        return self.cache
    
    def save(self) -> bool:
        """Save cache to file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.cache_file:
            return False
            
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # Update last build time
        self.cache["last_build"] = datetime.datetime.now().isoformat()
        
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            self.dirty = False
            return True
        except OSError as e:
            log.error(f"Error saving build cache: {e}")
            return False
    
    def check_and_reset_rebuild_status(self) -> bool:
        """Check if a rebuild has been requested and reset the flag.
        
        Returns:
            bool: True if rebuild was requested, False otherwise
        """
        rebuild = self.cache.get("rebuild_flag", False)
        
        # Reset the flag if it was set
        if rebuild:
            self.cache["rebuild_flag"] = False
            self.dirty = True
            self.save()
            
        return rebuild
    
    def set_rebuild_needed(self) -> None:
        """Mark that a rebuild is needed."""
        self.cache["rebuild_flag"] = True
        self.dirty = True
        self.save()
    
    def _preprocess_paths_for_json(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Path objects to strings for JSON serialization.
        
        Args:
            config: Configuration dictionary that may contain Path objects
            
        Returns:
            Dict with Path objects converted to strings
        """
        processed_config = {}
        
        for key, value in config.items():
            if isinstance(value, Path):
                processed_config[key] = str(value)
            elif isinstance(value, dict):
                processed_config[key] = self._preprocess_paths_for_json(value)
            elif isinstance(value, list):
                processed_config[key] = [
                    str(item) if isinstance(item, Path) else 
                    self._preprocess_paths_for_json(item) if isinstance(item, dict) else 
                    item 
                    for item in value
                ]
            else:
                processed_config[key] = value
                
        return processed_config
