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
- Ninja build system (optional, for faster builds)

### Install from GitHub (recommended)

To install directly from GitHub, run:

```bash
# Clone the repository
git clone https://github.com/naxzyu/ares-engine.git
cd ares-engine

# Create a virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate  # For Linux/macOS: source .venv/bin/activate

# Install in development mode with all dependencies
pip install -e .
```

## Building the Engine

```bash
# Build the engine
ares build engine
```

## Building a Project

```bash
# Build an example project
ares build examples\hello_world

# Force rebuilding a project
ares build your\project\path --force

# Cleaning your build
ares clean
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

## License

This dataset is licensed under the [Apache 2.0 License](LICENSE)

## Citations

Please use the following BibTeX entry to cite this dataset:

```bibtex
@software{ares-engine,
  author = {Kara Rawson},
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
