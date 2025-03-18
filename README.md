# Ares Engine

A cross-platform Vulkan game engine with Cython acceleration.

## Features

- SDL2-based windowing and input system
- Cython-accelerated math and physics operations
- Vulkan rendering support
- Modern Python (3.12+) codebase
- Comprehensive configuration system

## Installation

### Requirements

- Python 3.12 or higher
- C++ compiler (Visual Studio, GCC, Clang)
- Ninja build system (optional, for faster builds)

### Installation Options

#### Option 1: Install directly from GitHub (recommended)

```bash
# Install directly from GitHub
pip install git+https://github.com/naxzyu/ares-engine.git
```

You can also add it to your project's requirements.txt:

#### Option 2: Using setup.py (recommended for development)

```bash
# Clone the repository
git clone https://github.com/naxzyu/ares-engine.git
cd ares-engine

# Or use the setup utility (which will create a virtual environment for you)
python setup.py
```

## Usage

```python
import ares

# Create a window
window = ares.Window("My Game", 1280, 720)
window.show()

# Create input handler
input_system = ares.Input()

# Main loop
while window.running:
    # Process window events
    if not window.process_events():
        break
    
    # Update input state
    input_system.update()
    
    # Your game logic here...
    
    # Close with Escape key
    if input_system.is_key_pressed(ares.sdl2.SDL_SCANCODE_ESCAPE):
        window.close()

# Clean up
window.close()
```

## Configuration

Engine configuration is stored in INI files:

- `engine.ini` - Core engine settings
- `build.ini` - Build and compilation settings

Settings are automatically loaded at startup, and can be accessed through the configuration API:

```python
from ares.config import engine_config, build_config

# Get current display resolution
width, height = engine_config.get_resolution()

# Change fullscreen mode
engine_config.set_fullscreen(True)
engine_config.save()  # Save changes

# Get build version
version = build_config.get_version_string()
```

## License

[Apache 2.0 License](LICENSE)
