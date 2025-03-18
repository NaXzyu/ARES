import time
import ares
import sdl2

def main():
    window = ares.Window("Ares Engine - Hello World", 800, 600)
    window.show()
    
    input_handler = ares.Input()
    
    frame_count = 0
    start_time = time.time()
    
    while window.running:
        if not window.process_events():
            break
            
        input_handler.update()
        
        if input_handler.is_key_pressed(sdl2.SDL_SCANCODE_ESCAPE):
            break
            
        if frame_count % 60 == 0:
            mouse_x, mouse_y = input_handler.get_mouse_position()
            print(f"Mouse position: {mouse_x}, {mouse_y}")
            
        frame_count += 1
        
        time.sleep(0.016)
    
    elapsed = time.time() - start_time
    print(f"Average FPS: {frame_count / elapsed:.2f}")
    
    window.close()

if __name__ == "__main__":
    main()
