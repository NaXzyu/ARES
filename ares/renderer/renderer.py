"""
High-level rendering interface for Ares Engine.
This serves as a facade for the underlying rendering implementations.
"""

from .vulkan import VulkanRenderer

class Renderer:
    """High-level rendering interface that delegates to a specific implementation."""
    
    def __init__(self, backend='vulkan'):
        """Initialize the renderer with the specified backend.
        
        Args:
            backend: The rendering backend to use ('vulkan' only currently supported)
        """
        self.backend = backend
        self.implementation = None
        
    def initialize(self, window):
        """Initialize the renderer with the given window.
        
        Args:
            window: An instance of Window from ares.core.window
        """
        if self.backend == 'vulkan':
            self.implementation = VulkanRenderer()
            self.implementation.initialize(window)
        else:
            raise ValueError(f"Unsupported renderer backend: {self.backend}")
    
    def render(self, scene):
        """Render a scene.
        
        Args:
            scene: The scene to render
        """
        if self.implementation:
            self.implementation.render(scene)
    
    def begin_frame(self):
        """Begin a new frame."""
        if hasattr(self.implementation, 'begin_frame'):
            self.implementation.begin_frame()
    
    def end_frame(self):
        """End the current frame and present it."""
        if hasattr(self.implementation, 'end_frame'):
            self.implementation.end_frame()
    
    def cleanup(self):
        """Clean up rendering resources."""
        if self.implementation:
            self.implementation.cleanup()
            self.implementation = None
