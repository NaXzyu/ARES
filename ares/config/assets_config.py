"""
Asset configuration settings for the Ares Engine project.
"""

from .base_config import BaseConfig

class AssetsConfig(BaseConfig):

    def __init__(self):
        super().__init__("assets")
        self._create_default_config()

    def _create_default_config(self):
        """Create default asset configuration."""
        self.set("assets", "compress_textures", "True")
        self.set("assets", "audio_quality", "medium")
        self.set("assets", "bundle_assets", "True")
        self.set("assets", "exclude_patterns", "*.psd, *.xcf, *.blend, *.max, *.mb, *.ma, *.fbx")
        self.set("assets", "include_source_maps", "False")
        self.set("assets", "convert_models", "True")
        self.set("assets", "optimize_assets", "True")
        self.set("assets", "asset_compression", "zlib")
    
    def should_compress_textures(self):
        """Check if texture compression is enabled."""
        return self.getboolean("assets", "compress_textures", True)
    
    def get_audio_quality(self):
        """Get the audio quality setting."""
        return self.get("assets", "audio_quality", "medium")
    
    def should_bundle_assets(self):
        """Check if assets should be bundled with the executable."""
        return self.getboolean("assets", "bundle_assets", True)
    
    def get_exclude_patterns(self):
        """Get list of file patterns to exclude from asset processing."""
        patterns = self.get("assets", "exclude_patterns", "")
        return [p.strip() for p in patterns.split(",") if p.strip()]
    
    def get_asset_compression(self):
        """Get asset compression method."""
        return self.get("assets", "asset_compression", "zlib")
    
    def get_override_dict(self):
        """Get dictionary of important configuration values."""
        return {
            "compress_textures": self.should_compress_textures(),
            "audio_quality": self.get_audio_quality(),
            "bundle_assets": self.should_bundle_assets(),
            "exclude_patterns": self.get_exclude_patterns(),
            "asset_compression": self.get_asset_compression(),
            "optimize_assets": self.getboolean("assets", "optimize_assets", True)
        }
    
    def initialize(self, *args, **kwargs):
        """Initialize this configuration."""
        return True
