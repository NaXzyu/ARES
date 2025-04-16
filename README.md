# ARES

ARES is a cross-platform, modular game engine written in Python 3.12+ with Cython GPU acceleration and Vulkan rendering. It is designed for high performance, rapid iteration, and extensibility, focusing on 2D game development with future 3D support planned. Ares leverages Vulkan for advanced, ultra-fast, and open graphics.

## Features

- **Vulkan Rendering:** Advanced, ultra-fast, and open graphics via Vulkan backend.
- **Cython Acceleration:** High-performance math and physics operations.
- **Cross-Platform:** Windows, Linux, and macOS support.
- **Modern Python (3.12+):** Clean, maintainable codebase.
- **ECS Architecture:** Entity Component System for scalable, maintainable game logic.
- **Integrated Tooling:** Scene and dialog editors (planned), asset management, and CLI utilities.
- **Flexible Configuration:** Layered INI-based system for project, build, and engine settings.
- **Automated Build & Packaging:** OS-independent builds, asset bundling, and PyInstaller integration.
- **Comprehensive Logging & Telemetry:** Debugging, profiling, and CI integration.
- **State Management:** Hierarchical FSM for complex behaviors.
- **User Interface:** Basic UI system for dialog and menus.
- **Interaction System:** Player-NPC and world object interaction support.
- **Ultra-fast Incremental Build System:** Efficient artifact tracking and rebuilds.

## Installation

### Requirements

- Python 3.12 or higher
- C++ compiler (Visual Studio, GCC, Clang, LLVM)

### Install from GitHub (recommended)

```bash
# Clone the repository
git clone https://github.com/NaXzyu/ARES.git
cd ARES

# Create a virtual environment
uv venv --python=3.12

# Activate your environment
.venv\Scripts\activate  # For Linux/macOS: source .venv/bin/activate

# Install in development mode with all dependencies
uv pip install -e .[dev]
```

## Building the Engine

```bash
# Build the engine
uv run ares build engine
```

## Building a Project

```bash
# Build an example project
uv run ares build examples\hello_world

# Force rebuilding a project
uv run ares build your\project\path --force

# Clean your build
uv run ares clean
```

## Usage

Below is a minimal example of using Ares Engine:

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

This project is licensed under the [Apache 2.0 License](LICENSE).

## Citation

If you use Ares Engine in your research or projects, please cite:

```bibtex
@software{ares-engine,
  author = {K. Rawson},
  title = {ARES: A cross-platform Vulkan game engine with Cython GPU acceleration},
  year = {2026},
  howpublished = {\url{https://github.com/NaXzyu/ARES}},
  note = {Accessed: 2026-01-26}
}
```

## Contact

For questions or support, please contact:

- **Email**: <backrqqms@gmail.com>
- **Discord**: [Join our Discord](https://discord.gg/2xpqjDUkHD)
