"""
Engine configuration settings for the Ares Engine.
"""

from .base_config import BaseConfig

class EngineConfig(BaseConfig):
    
    def __init__(self):
        super().__init__("engine")
        self._create_default_config()
        
    def _create_default_config(self):
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
        
        self.set("audio", "master_volume", "0.8")
        self.set("audio", "music_volume", "0.7")
        self.set("audio", "sfx_volume", "1.0")
        self.set("audio", "voice_volume", "0.9")
        self.set("audio", "mute", "False")
        self.set("audio", "audio_device", "default")
        self.set("audio", "audio_channels", "32")
        self.set("audio", "spatial_audio", "True")
        self.set("audio", "sample_rate", "48000")
        
        self.set("input", "mouse_sensitivity", "1.0")
        self.set("input", "invert_y", "False")
        self.set("input", "controller_enabled", "True")
        self.set("input", "controller_vibration", "True")
        self.set("input", "controller_deadzone", "0.1")
        self.set("input", "key_mapping", "default")
        
        self.set("physics", "timestep", "0.016")
        self.set("physics", "gravity", "9.81")
        self.set("physics", "simulation_quality", "medium")
        self.set("physics", "max_objects", "1000")
        self.set("physics", "collision_precision", "medium")
        self.set("physics", "use_multithreaded_physics", "True")
        
        self.set("debug", "logging_level", "info")
        self.set("debug", "show_fps", "False")
        self.set("debug", "show_debug_info", "False")
        self.set("debug", "console_enabled", "False")
        self.set("debug", "profiler_enabled", "False")
        self.set("debug", "memory_tracking", "False")
    
    def get_resolution(self):
        width = self.getint("graphics", "resolution_width", 1280)
        height = self.getint("graphics", "resolution_height", 720)
        return (width, height)
    
    def set_resolution(self, width, height):
        self.set("graphics", "resolution_width", str(width))
        self.set("graphics", "resolution_height", str(height))
    
    def is_fullscreen(self):
        return self.getboolean("graphics", "fullscreen", False)
    
    def set_fullscreen(self, enabled):
        self.set("graphics", "fullscreen", str(enabled))
    
    def get_master_volume(self):
        return self.getfloat("audio", "master_volume", 0.8)
    
    def set_master_volume(self, volume):
        self.set("audio", "master_volume", str(max(0.0, min(1.0, volume))))
