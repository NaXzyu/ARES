import sys
from ares.core.window import Window
from ares.core.input import Input
import sdl2

def main():
    # Create a window
    window = Window("Ares Engine - Hello World", 800, 600)
    window.show()
    
    # Setup input handling
    input_handler = Input()
    
    # Simple main loop
    while window.running:
        # Process window events (includes checking for close button)
        if not window.process_events():
            break
            
        # Update input state
        input_handler.update()
        
        # Check for escape key to exit
        if input_handler.is_key_pressed(sdl2.SDL_SCANCODE_ESCAPE):
            break
        
        # Draw the frame
        window.present()
    
    # Clean up
    window.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
