"""
Input handling system for keyboard, mouse, and gamepads.
"""
import sdl2
import logging

class Input:
    def __init__(self):
        self.event = sdl2.SDL_Event()
        self.keyboard_state = sdl2.SDL_GetKeyboardState(None)
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_buttons = [False, False, False]
        
        # Add action mapping (similar to Mars X)
        self.actions = {
            'move_forward': False,
            'move_backward': False,
            'move_left': False,
            'move_right': False,
            'jump': False,
            'fire': False,
            'toggle_fullscreen': False,
            'quit': False
        }
        
        # Key mappings for game actions
        self.key_mappings = {
            'move_forward': sdl2.SDLK_w,
            'move_backward': sdl2.SDLK_s,
            'move_left': sdl2.SDLK_a,
            'move_right': sdl2.SDLK_d,
            'jump': sdl2.SDLK_SPACE,
            'fire': sdl2.SDLK_LCTRL,
            'toggle_fullscreen': sdl2.SDLK_F11,
            'quit': sdl2.SDLK_ESCAPE
        }
        
        # Track one-time actions
        self.key_just_pressed = {action: False for action in self.actions}
        
    def process_events(self):
        """Process all pending SDL events and update input state.
        
        Returns:
            bool: True if the application should continue, False if quit was requested.
        """
        quit_requested = False
        
        # Reset one-time actions
        for action in self.key_just_pressed:
            self.key_just_pressed[action] = False
        
        # Poll all events
        while sdl2.SDL_PollEvent(self.event):
            # Handle mouse motion
            if self.event.type == sdl2.SDL_MOUSEMOTION:
                self.mouse_x = self.event.motion.x
                self.mouse_y = self.event.motion.y
            
            # Handle mouse buttons
            elif self.event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                if self.event.button.button == sdl2.SDL_BUTTON_LEFT:
                    self.mouse_buttons[0] = True
                elif self.event.button.button == sdl2.SDL_BUTTON_MIDDLE:
                    self.mouse_buttons[1] = True
                elif self.event.button.button == sdl2.SDL_BUTTON_RIGHT:
                    self.mouse_buttons[2] = True
                    
            elif self.event.type == sdl2.SDL_MOUSEBUTTONUP:
                if self.event.button.button == sdl2.SDL_BUTTON_LEFT:
                    self.mouse_buttons[0] = False
                elif self.event.button.button == sdl2.SDL_BUTTON_MIDDLE:
                    self.mouse_buttons[1] = False
                elif self.event.button.button == sdl2.SDL_BUTTON_RIGHT:
                    self.mouse_buttons[2] = False
            
            # Handle key events
            elif self.event.type == sdl2.SDL_KEYDOWN:
                key = self.event.key.keysym.sym
                
                # Update action states based on key mappings
                for action, mapped_key in self.key_mappings.items():
                    if key == mapped_key:
                        self.actions[action] = True
                        self.key_just_pressed[action] = True
                        
                        # Handle special case for fullscreen toggle
                        if action == 'toggle_fullscreen' and self.key_just_pressed[action]:
                            # The window will need to handle this separately
                            pass
                
            elif self.event.type == sdl2.SDL_KEYUP:
                key = self.event.key.keysym.sym
                
                # Update action states based on key mappings
                for action, mapped_key in self.key_mappings.items():
                    if key == mapped_key:
                        self.actions[action] = False
                        
            # Handle quit event (window close)
            elif self.event.type == sdl2.SDL_QUIT:
                self.actions['quit'] = True
                quit_requested = True
        
        # Update keyboard state
        self.keyboard_state = sdl2.SDL_GetKeyboardState(None)
        
        # Check if quit action was triggered
        if self.actions['quit']:
            quit_requested = True
            
        return not quit_requested  # Return True to continue, False to quit
        
    def update(self):
        """Legacy method for compatibility. Use process_events() instead."""
        self.process_events()
        
    def is_key_pressed(self, key):
        """Check if a key is currently pressed."""
        return bool(self.keyboard_state[key])
        
    def get_mouse_position(self):
        """Get the current mouse position."""
        return (self.mouse_x, self.mouse_y)
        
    def is_mouse_button_pressed(self, button):
        """Check if a mouse button is currently pressed."""
        return self.mouse_buttons[button]
        
    def is_action_active(self, action):
        """Check if a game action is currently active."""
        return self.actions.get(action, False)
    
    def is_action_just_pressed(self, action):
        """Check if a game action was just pressed this frame."""
        return self.key_just_pressed.get(action, False)
