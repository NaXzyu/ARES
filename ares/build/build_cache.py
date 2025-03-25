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
        with open(cache_file, "w") as f:
            json.dump(cache, f, indent=2)
    except IOError as e:
        log.warn(f"Warning: Failed to save build cache: {e}")

def set_cache_paths(build_dir):
    """Update the global cache paths based on a custom build directory.
    
    Args:
        build_dir: Custom build directory path
    """
    global CACHE_DIR, BUILD_CACHE_FILE
    CACHE_DIR = Path(build_dir) / "cache"
    BUILD_CACHE_FILE = CACHE_DIR / "build_cache.json"
    return CACHE_DIR, BUILD_CACHE_FILE
