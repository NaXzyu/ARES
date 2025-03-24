"""
Rendering system with Vulkan support.
"""

from __future__ import annotations

# Import primary components
from .renderer import Renderer
from .vulkan import VulkanRenderer

# Define what gets imported with "from ares.renderer import *"
__all__ = [
    'Renderer',
    'VulkanRenderer'
]
