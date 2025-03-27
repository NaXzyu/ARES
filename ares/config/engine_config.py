"""
Engine configuration settings for the Ares Engine project.
"""

from .base_config import BaseConfig

class EngineConfig(BaseConfig):

    def __init__(self):
        super().__init__("engine")
        self._create_default_config()
        
    def _create_default_config(self):
        """Create default engine configuration."""
        # Graphics section
        self.set("graphics", "resolution_width", "1280")
        self.set("graphics", "resolution_height", "720")
        self.set("graphics", "fullscreen", "False")
        self.set("graphics", "vsync", "True")
        self.set("graphics", "max_fps", "60")
        self.set("graphics", "texture_quality", "high")
        self.set("graphics", "shadows", "True")
        self.set("graphics", "shadow_quality", "medium")
        self.set("graphics", "anti_aliasing", "True")
        self.set("graphics", "anti_aliasing_level", "4")
        self.set("graphics", "anisotropic_filtering", "4")
        self.set("graphics", "post_processing", "True")
        
        # Audio section
        self.set("audio", "master_volume", "0.8")
        self.set("audio", "music_volume", "0.7")
        self.set("audio", "sfx_volume", "1.0")
        self.set("audio", "voice_volume", "0.9")
        self.set("audio", "mute", "False")
        self.set("audio", "audio_device", "default")
        self.set("audio", "audio_channels", "32")
        self.set("audio", "spatial_audio", "True")
        self.set("audio", "sample_rate", "48000")
        
        # Input section
        self.set("input", "mouse_sensitivity", "1.0")
        self.set("input", "invert_y", "False")
        self.set("input", "controller_enabled", "True")
        self.set("input", "controller_vibration", "True")
        self.set("input", "controller_deadzone", "0.1")
        self.set("input", "key_mapping", "default")
        
        # Physics section
        self.set("physics", "timestep", "0.016")
        self.set("physics", "gravity", "9.81")
        self.set("physics", "simulation_quality", "medium")
        self.set("physics", "max_objects", "1000")
        self.set("physics", "collision_precision", "medium")
        self.set("physics", "use_multithreaded_physics", "True")
        
        # Debug section
        self.set("debug", "logging_level", "info")
        self.set("debug", "show_fps", "False")
        self.set("debug", "show_debug_info", "False")
        self.set("debug", "console_enabled", "False")
        self.set("debug", "profiler_enabled", "False")
        self.set("debug", "memory_tracking", "False")
    
    def get_resolution(self):
        """Get the configured resolution as a tuple (width, height)."""
        width = self.getint("graphics", "resolution_width", 1280)
        height = self.getint("graphics", "resolution_height", 720)
        return (width, height)
    
    def is_fullscreen(self):
        """Check if fullscreen mode is enabled."""
        return self.getboolean("graphics", "fullscreen", False)
    
    def is_vsync_enabled(self):
        """Check if vertical sync is enabled."""
        return self.getboolean("graphics", "vsync", True)
    
    def get_max_fps(self):
        """Get the maximum frames per second setting."""
        return self.getint("graphics", "max_fps", 60)
    
    def get_physics_timestep(self):
        """Get the physics engine timestep in seconds."""
        return self.getfloat("physics", "timestep", 0.016)
    
    def get_gravity(self):
        """Get the gravitational acceleration value."""
        return self.getfloat("physics", "gravity", 9.81)
    
    def get_logging_level(self):
        """Get the configured logging level."""
        return self.get("debug", "logging_level", "info")
    
    def should_show_fps(self):
        """Check if FPS display is enabled."""
        return self.getboolean("debug", "show_fps", False)
    
    def get_master_volume(self):
        """Get the master volume level."""
        return self.getfloat("audio", "master_volume", 0.8)
    
    def is_audio_muted(self):
        """Check if audio is muted."""
        return self.getboolean("audio", "mute", False)
    
    def get_override_dict(self):
        """Get dictionary of important configuration values."""
        resolution = self.get_resolution()
        return {
            "resolution": f"{resolution[0]}x{resolution[1]}",
            "fullscreen": self.is_fullscreen(),
            "vsync": self.is_vsync_enabled(),
            "max_fps": self.get_max_fps(),
            "physics_timestep": self.get_physics_timestep(),
            "gravity": self.get_gravity(),
            "logging_level": self.get_logging_level(),
            "show_fps": self.should_show_fps(),
            "master_volume": self.get_master_volume(),
            "muted": self.is_audio_muted()
        }
    
    def initialize(self, *args, **kwargs):
        """Initialize this configuration."""
        return True
