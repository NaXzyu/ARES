"""
Rendering system with Vulkan support.
"""

from __future__ import annotations

# Import primary components
from .vulkan import VulkanRenderer

# Define default renderer
Renderer = VulkanRenderer

# Define what gets imported with "from ares.renderer import *"
__all__ = [
    'VulkanRenderer',
    'Renderer'
]
