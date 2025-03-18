"""
Input handling system for keyboard, mouse, and gamepads.
"""
import sdl2

class Input:
    def __init__(self):
        self.keyboard_state = sdl2.SDL_GetKeyboardState(None)
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_buttons = [False, False, False]
        
    def update(self):
        mouse_x_ptr = sdl2.c_int(0)
        mouse_y_ptr = sdl2.c_int(0)
        button_state = sdl2.SDL_GetMouseState(sdl2.byref(mouse_x_ptr), sdl2.byref(mouse_y_ptr))
        self.mouse_x = mouse_x_ptr.value
        self.mouse_y = mouse_y_ptr.value
        
        self.mouse_buttons[0] = bool(button_state & sdl2.SDL_BUTTON_LMASK)
        self.mouse_buttons[1] = bool(button_state & sdl2.SDL_BUTTON_MMASK)
        self.mouse_buttons[2] = bool(button_state & sdl2.SDL_BUTTON_RMASK)
        
    def is_key_pressed(self, key):
        return bool(self.keyboard_state[key])
        
    def get_mouse_position(self):
        return (self.mouse_x, self.mouse_y)
        
    def is_mouse_button_pressed(self, button):
        return self.mouse_buttons[button]
