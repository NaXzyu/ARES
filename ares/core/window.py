"""
Window management system using SDL2.
"""
import sdl2
import sdl2.ext

class Window:
    def __init__(self, title="Ares Engine", width=800, height=600):
        sdl2.ext.init()
        self.window = sdl2.ext.Window(title, size=(width, height))
        self.running = False
        
    def show(self):
        self.window.show()
        self.running = True
        
    def hide(self):
        self.window.hide()
        
    def process_events(self):
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                self.running = False
                return False
        return True
        
    def close(self):
        self.running = False
        self.window.close()
        sdl2.ext.quit()
