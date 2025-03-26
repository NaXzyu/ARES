# Ares Engine

A cross-platform Vulkan game engine with Cython GPU acceleration.

## Features

- SDL2-based windowing and input system
- Cython-accelerated math and physics operations
- Vulkan rendering support
- Modern Python (3.12+) codebase
- Comprehensive configuration system
- OS Independent builds & executables
- Parallel CPU cores with multi-threading support
- Built-in CUDA and AMD support
- 🔥Ultra-fast incremental build system

## Installation

### Requirements

- Python 3.12 or higher
- C++ compiler (Visual Studio, GCC, Clang)
- Ninja build system (optional, for parallel builds)

#### Install from GitHub (recommended)

To install directly from GitHub, run:

```bash
pip install git+https://github.com/naxzyu/ares-engine.git
```

You can also add it to your project's requirements.txt.

### Building

You may also choose to build the engine from the orginal source code from scratch. This is a relatively easy process if you follow the steps below:

#### Using setup.py (recommended for development)

Clone the repository and run the setup utility:

```bash
git clone https://github.com/naxzyu/ares-engine.git
cd ares-engine

# Creates a virtual environment automatically.
python setup.py

# Build the engine
python setup.py --build
```

## Usage

The follow code snippets are examples of how to use Ares Engine:

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

The configuration for Ares Engine is very straight-forward and modular. The Engine configuration is stored in INI files:

- `engine.ini` - Core engine settings
- `build.ini` - Build and compilation settings
- `package.ini` - Source code definitions

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

This dataset is licensed under the [Apache 2.0 License](LICENSE)

## Citations

Please use the following BibTeX entry to cite this dataset:

```bibtex
@software{ares-engine,
  author = {Kara Rawson, Aimee Chrzanowski},
  title = {Ares Engine: A cross-platform Vulkan game engine with Cython GPU acceleration},
  year = {2025},
  howpublished = {\url{https://github.com/NaXzyu/ares-engine}},
  note = {Accessed: 2026-01-26}
}
```

## Contact

For questions or support, please contact us at:

- **Email**: <backrqqms@gmail.com>
- **Discord**: [Join our Discord](https://discord.gg/2xpqjDUkHD)
