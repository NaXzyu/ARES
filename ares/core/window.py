"""Window management system using SDL2."""
import logging
import sdl2
import sdl2.ext

class Window:
    """Window class for rendering graphics using SDL2."""
    
    def __init__(self, title="Ares Engine", width=800, height=600):
        """Initialize a window with the specified parameters."""
        sdl2.ext.init()
        
        # Store parameters
        self.title = title.encode('utf-8') if isinstance(title, str) else title
        self.width = width
        self.height = height
        self.running = True
        self.is_fullscreen = False
        
        # Create SDL window directly using the sdl2.ext approach which is more consistent
        # This avoids the from_window() method which may not be available in all SDL2 versions
        self.ext_window = sdl2.ext.Window(
            title,
            size=(width, height),
            flags=sdl2.SDL_WINDOW_RESIZABLE | 
                 (sdl2.SDL_WINDOW_VULKAN if hasattr(sdl2, 'SDL_WINDOW_VULKAN') else 0)
        )
        self.window = self.ext_window.window
        
        if not self.window:
            raise RuntimeError(f"Failed to create SDL window: {sdl2.SDL_GetError().decode()}")
        
        # Create a renderer
        self.renderer = sdl2.ext.Renderer(self.ext_window)
        
        # Set default background color to black
        self.renderer.color = sdl2.ext.Color(0, 0, 0, 255)
    
    def get_sdl_window(self):
        """Get the underlying SDL window handle."""
        return self.window
    
    def get_size(self):
        """Get the current window size."""
        w = sdl2.c_int()
        h = sdl2.c_int()
        sdl2.SDL_GetWindowSize(self.window, w, h)
        return (w.value, h.value)
    
    def show(self):
        """Show the window and render initial frame."""
        self.renderer.clear()
        self.renderer.present()
        self.running = True
        
    def hide(self):
        """Hide the window."""
        sdl2.SDL_HideWindow(self.window)
    
    def toggle_fullscreen(self):
        """Toggle between windowed and fullscreen modes."""
        self.is_fullscreen = not self.is_fullscreen
        flags = sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP if self.is_fullscreen else 0
        sdl2.SDL_SetWindowFullscreen(self.window, flags)
        
        # Get updated window size after toggle
        self.width, self.height = self.get_size()
        return self.is_fullscreen
        
    def process_events(self):
        """Legacy method that processes SDL events directly.
        
        This is maintained for backward compatibility. New code should use
        an Input object to process events.
        
        Returns:
            bool: True if the application should continue, False if quit was requested.
        """
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(event):
            if event.type == sdl2.SDL_QUIT:
                self.running = False
                return False
            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_F11:
                    self.toggle_fullscreen()
                elif event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    self.running = False
                    return False
            elif event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
                    self.width = event.window.data1
                    self.height = event.window.data2
        
        return True
    
    def handle_input(self, input_handler):
        """Process events using an Input handler.
        
        Args:
            input_handler: An instance of Input from ares.core.input
            
        Returns:
            bool: True if the application should continue, False if quit was requested.
        """
        # Let input handler process events
        continue_running = input_handler.process_events()
        self.running = continue_running
        
        # Check for toggle fullscreen action
        if input_handler.is_action_just_pressed('toggle_fullscreen'):
            self.toggle_fullscreen()
            
        return continue_running
    
    def clear(self, r=0, g=0, b=0):
        """Clear the window to the specified color."""
        self.renderer.color = sdl2.ext.Color(r, g, b)
        self.renderer.clear()
    
    def present(self):
        """Present the current frame to the screen."""
        self.renderer.present()
    
    def close(self):
        """Close the window and clean up resources."""
        self.running = False
        if self.window:
            sdl2.SDL_DestroyWindow(self.window)
            self.window = None
        
        # Only quit SDL if we initialized it
        if sdl2.SDL_WasInit(sdl2.SDL_INIT_VIDEO):
            sdl2.SDL_Quit()
            
    # Additional Vulkan-related methods for future compatibility
    def get_vulkan_instance_extensions(self):
        """Get required Vulkan instance extensions for this window."""
        if not hasattr(sdl2, 'SDL_Vulkan_GetInstanceExtensions'):
            return []
            
        try:
            extension_count = sdl2.c_uint32(0)
            sdl2.SDL_Vulkan_GetInstanceExtensions(self.window, extension_count, None)
            
            extensions = (sdl2.c_char_p * extension_count.value)()
            sdl2.SDL_Vulkan_GetInstanceExtensions(self.window, extension_count, extensions)
            
            return [extensions[i].decode() for i in range(extension_count.value)]
        except Exception as e:
            logging.warning(f"Failed to get Vulkan instance extensions: {e}")
            return []
    
    def create_vulkan_surface(self, instance):
        """Create a Vulkan surface for this window."""
        if not hasattr(sdl2, 'SDL_Vulkan_CreateSurface'):
            return None
            
        try:
            surface = sdl2.vk.VkSurfaceKHR()
            if not sdl2.SDL_Vulkan_CreateSurface(self.window, instance, surface):
                raise RuntimeError(f"Failed to create Vulkan surface: {sdl2.SDL_GetError().decode()}")
            return surface
        except Exception as e:
            logging.warning(f"Failed to create Vulkan surface: {e}")
            return None
