"""Build cache management for Ares Engine build system."""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any

from ares.utils.log import log
from ares.utils.paths import Paths


class BuildCache:
    """Manages build cache for incremental builds using singleton pattern."""
    
    # Singleton instance
    _instance = None
    _initialized = False

    # Cache data
    _cache = None
    _cache_file = None
    _cache_dir = None
    
    def __new__(cls, cache_file: Optional[Path] = None, cache_dir: Optional[Path] = None):
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super(BuildCache, cls).__new__(cls)
            cls._instance._init(cache_file, cache_dir)
        elif cache_file is not None or cache_dir is not None:
            cls._instance._init(cache_file, cache_dir)
        return cls._instance
    
    def _init(self, cache_file: Optional[Path] = None, cache_dir: Optional[Path] = None):
        """Initialize the build cache (internal method).
        
        Args:
            cache_file: Optional custom cache file path
            cache_dir: Optional custom cache directory path
        """
        if not BuildCache._initialized or cache_file is not None or cache_dir is not None:
            BuildCache._cache_file = cache_file or Paths.get_build_cache_file()
            BuildCache._cache_dir = cache_dir or Paths.get_cache_path()
            BuildCache._cache = self.load()
            BuildCache._initialized = True
    
    @property
    def cache(self) -> Dict[str, Any]:
        """Access the cache data."""
        return BuildCache._cache
    
    @cache.setter
    def cache(self, value: Dict[str, Any]):
        """Set the cache data."""
        BuildCache._cache = value
    
    @property
    def cache_file(self) -> Path:
        """Access the cache file path."""
        return BuildCache._cache_file
    
    @property
    def cache_dir(self) -> Path:
        """Access the cache directory path."""
        return BuildCache._cache_dir
    
    def load(self) -> Dict[str, Any]:
        """Load the build cache from the cache file if it exists.
        
        Returns:
            The loaded cache as a dictionary, or a new empty cache if loading failed
        """
        if not BuildCache._cache_file.exists():
            return {"files": {}, "last_build": None}
        
        try:
            with open(BuildCache._cache_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            log.warn(f"Warning: Failed to load build cache: {e}")
            return {"files": {}, "last_build": None}
    
    def save(self) -> str:
        """Save the build cache to the cache file.
        
        Returns:
            ISO format timestamp of when the cache was saved
        """
        import datetime
        
        # Update the last build timestamp
        timestamp = datetime.datetime.now().isoformat()
        BuildCache._cache["last_build"] = timestamp
        
        os.makedirs(BuildCache._cache_dir, exist_ok=True)
        try:
            # Preprocess paths for JSON serialization
            processed_cache = self._preprocess_paths_for_json(BuildCache._cache)
            with open(BuildCache._cache_file, "w") as f:
                json.dump(processed_cache, f, indent=2)
        except IOError as e:
            log.warn(f"Warning: Failed to save build cache: {e}")
        
        return timestamp
    
    @staticmethod
    def _preprocess_paths_for_json(obj: Any) -> Any:
        """Convert any Path objects in a nested structure to strings for JSON serialization.
        
        Args:
            obj: The object to process (can be dict, list, Path, etc.)
            
        Returns:
            The processed object with Path objects converted to strings
        """
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: BuildCache._preprocess_paths_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [BuildCache._preprocess_paths_for_json(item) for item in obj]
        else:
            return obj
    
    @classmethod
    def set_cache_paths(cls, build_dir: Path) -> tuple[Path, Path]:
        """Update the cache paths based on a custom build directory.
        
        Args:
            build_dir: Custom build directory path
            
        Returns:
            Tuple containing (cache_dir, cache_file) paths
        """
        cache_dir = Paths.get_cache_path()
        build_cache_file = Paths.get_build_cache_file()
        
        # Update the singleton paths
        if cls._instance:
            cls._instance._init(build_cache_file, cache_dir)
            
        return cache_dir, build_cache_file
    
    def check_and_reset_rebuild_status(self) -> bool:
        """Check if modules were rebuilt and reset the status in the cache.
        
        Returns:
            bool: True if modules were rebuilt, False otherwise
        """
        # Check if modules were rebuilt
        modules_rebuilt = BuildCache._cache.get("rebuilt_modules", False)
        
        # Reset the status in the cache
        if modules_rebuilt:
            BuildCache._cache["rebuilt_modules"] = False
            self.save()
        
        return modules_rebuilt
    
    @classmethod
    def get_instance(cls) -> 'BuildCache':
        """Get or create the singleton instance.
        
        Returns:
            The singleton BuildCache instance
        """
        if cls._instance is None:
            cls._instance = BuildCache()
        return cls._instance
