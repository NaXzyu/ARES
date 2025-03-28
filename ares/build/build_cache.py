"""Build cache management for Ares Engine build system."""

import os
import json
from pathlib import Path

from ares.utils import log

# Default locations - these can be overridden by the caller
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BUILD_DIR = PROJECT_ROOT / "build"
CACHE_DIR = BUILD_DIR / "cache"
BUILD_CACHE_FILE = CACHE_DIR / "build_cache.json"

def load_build_cache(cache_file=None):
    """Load the build cache from the cache file if it exists.
    
    Args:
        cache_file: Optional custom cache file path
        
    Returns:
        dict: The loaded cache as a dictionary, or a new empty cache if loading failed
    """
    if cache_file is None:
        cache_file = BUILD_CACHE_FILE
        
    if not cache_file.exists():
        return {"files": {}, "last_build": None}
    
    try:
        with open(cache_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log.warn(f"Warning: Failed to load build cache: {e}")
        return {"files": {}, "last_build": None}

def save_build_cache(cache, cache_file=None, cache_dir=None):
    """Save the build cache to the cache file.
    
    Args:
        cache: The cache dictionary to save
        cache_file: Optional custom cache file path
        cache_dir: Optional custom cache directory path
    """
    if cache_file is None:
        cache_file = BUILD_CACHE_FILE
        
    if cache_dir is None:
        cache_dir = CACHE_DIR
    
    os.makedirs(cache_dir, exist_ok=True)
    try:
        # Process any Path objects before saving
        processed_cache = _preprocess_paths_for_json(cache)
        with open(cache_file, "w") as f:
            json.dump(processed_cache, f, indent=2)
    except IOError as e:
        log.warn(f"Warning: Failed to save build cache: {e}")

def _preprocess_paths_for_json(obj):
    """Convert any Path objects in a nested structure to strings for JSON serialization.
    
    Args:
        obj: The object to process (can be dict, list, Path, etc.)
        
    Returns:
        The processed object with Path objects converted to strings
    """
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _preprocess_paths_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_preprocess_paths_for_json(item) for item in obj]
    else:
        return obj

def set_cache_paths(build_dir):
    """Update the global cache paths based on a custom build directory.
    
    Args:
        build_dir: Custom build directory path
    """
    global CACHE_DIR, BUILD_CACHE_FILE
    CACHE_DIR = Path(build_dir) / "cache"
    BUILD_CACHE_FILE = CACHE_DIR / "build_cache.json"
    return CACHE_DIR, BUILD_CACHE_FILE
