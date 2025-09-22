# PiCamera2 Core Module

This module provides the core implementation classes that form the foundation for the higher-level API interfaces.

## Overview

The core module contains the essential components that implement the fundamental camera operations. Most users will not need to interact with these classes directly, as they are abstracted by the high-level API classes.

## Key Components

### CameraCore

The fundamental camera implementation that wraps the original PiCamera2 class and provides:

- Camera initialization and configuration
- Resource management
- Access to the underlying PiCamera2 instance
- Camera information retrieval

```python
# Generally not used directly by end users
# But accessible if needed for advanced operations
camera = CameraController()
camera.initialize()

# Access the core implementation if needed
camera_core = camera.native
```

### ConfigurationManager

Manages camera configurations and provides predefined templates:

- Still capture configuration
- Video recording configuration
- Preview configuration
- High-resolution configuration
- Low-light configuration

```python
# Configuration is automatically handled by the high-level API
# But can be accessed for custom configurations
camera = CameraController()
camera.initialize()

# Example for using custom configuration
config = camera.native.create_still_configuration()
camera.configure(config)
```

## Internal Usage

These core components are primarily used internally by the API layer to implement the user-facing functionality. They handle the complex interactions with the PiCamera2 library while providing a solid foundation for the higher-level APIs.
