"""
Configuration manager for Ares Engine.

Provides utilities for working with the INI configuration files.
"""

import os
import configparser

from . import USER_CONFIG_DIR, CONFIG_FILES_DIR

class Config:
    def __init__(self):
        if not CONFIG_FILES_DIR.exists():
            os.makedirs(CONFIG_FILES_DIR, exist_ok=True)
        if not USER_CONFIG_DIR.exists():
            os.makedirs(USER_CONFIG_DIR, exist_ok=True)
        
        self.configs = {}
    
    def load(self, name):
        if name in self.configs:
            return self.configs[name]
            
        config = configparser.ConfigParser(comment_prefixes=('#', ';'))
        
        default_path = CONFIG_FILES_DIR / f"{name}.ini"
        user_path = USER_CONFIG_DIR / f"{name}.ini"
        
        loaded = False
        
        if default_path.exists():
            config.read(default_path)
            loaded = True
            print(f"Loaded default config from {default_path}")
            
        if user_path.exists():
            config.read(user_path)
            loaded = True
            print(f"Loaded user config from {user_path}")
            
        self.configs[name] = config
        return config
    
    def save(self, name, config=None):
        if config is None and name in self.configs:
            config = self.configs[name]
        elif config is None:
            raise ValueError(f"No config loaded with name '{name}'")
        
        user_path = USER_CONFIG_DIR / f"{name}.ini"
        os.makedirs(user_path.parent, exist_ok=True)
        
        with open(user_path, 'w') as f:
            config.write(f)
        
        print(f"Configuration saved to {user_path}")
    
    def get_value(self, config_name, section, option, fallback=None):
        config = self.load(config_name)
        if config.has_section(section):
            return config.get(section, option, fallback=fallback)
        return fallback
    
    def set_value(self, config_name, section, option, value):
        config = self.load(config_name)
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, option, value)
        return config
    
    def list_configs(self):
        config_files = [f.stem for f in CONFIG_FILES_DIR.glob("*.ini")]
        return config_files

config = Config()

def get_config():
    return config