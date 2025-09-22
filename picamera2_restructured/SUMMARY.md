# PiCamera2 Restructured - Module Summary

## Overview

PiCamera2 Restructured is a modular reimagining of the PiCamera2 library, designed to provide a clean, intuitive API while maintaining all the powerful functionality of the original library.

## Key Features

- **Simplified API**: Easy-to-use interface with logical method naming and organization
- **Modular Design**: Clean separation of concerns with specialized modules
- **Device-specific Optimizations**: Support for various camera modules and AI accelerators
- **Comprehensive Documentation**: Clear examples and explanations for all functionality
- **Flexible Configuration**: Simple presets with the ability to use advanced settings

## Module Structure

### API Module (`api/`)

The API module provides high-level interfaces for camera control:

- `CameraController`: The main entry point for all camera operations
- `CaptureAPI`: Handles image capture in various formats
- `PreviewAPI`: Manages camera preview in different modes
- `EncodingAPI`: Controls video recording and encoding

### Core Module (`core/`)

The core module implements the fundamental camera functionality:

- `CameraCore`: Base camera implementation
- `ConfigurationManager`: Handles camera configuration

### Devices Module (`devices/`)

The devices module provides device-specific implementations:

- `DeviceManager`: Detects and manages camera devices
- `IMX708Device`: Support for the Raspberry Pi Camera Module 3
- `IMX500Device`: Support for the Sony intelligent vision sensor
- `HailoDevice`: Support for Hailo AI accelerators

### Interfaces Module (`interfaces/`)

The interfaces module defines abstract interfaces for implementations:

- `CameraInterface`: Interface for camera implementations
- `DeviceInterface`: Interface for device-specific implementations

### Services Module (`services/`)

The services module provides specialized functionality:

- `capture/`: Services for image capture
- `preview/`: Services for camera preview
- `encoding/`: Services for video recording

### Utils Module (`utils/`)

The utils module provides utility functions:

- `ImageUtils`: Image processing utilities
- `FormatUtils`: Format-related utilities

## Usage Patterns

### Basic Usage

```python
from picamera2_restructured import CameraController

# Initialize camera
camera = CameraController()
camera.initialize()

# Capture an image
image = camera.capture.capture_image()

# Close camera
camera.close()
```

### Advanced Usage

```python
from picamera2_restructured import CameraController
from picamera2_restructured.utils import ImageUtils

# Initialize camera
camera = CameraController()
camera.initialize()

# Start preview
camera.preview.start()

# Use custom configuration
config = camera.native.create_still_configuration(main={"size": (4056, 3040)})
camera.configure(config)

# Capture and process image
image = camera.capture.capture_image(format='array')
processed = ImageUtils.add_timestamp(image)

# Close camera
camera.close()
```

## Extending the Library

The modular design makes it easy to extend the library:

1. Implement the appropriate interface(s)
2. Add your implementation to the relevant module
3. Update service or API classes to use your implementation

For example, to add support for a new camera module:

```python
from picamera2_restructured.devices import BaseDevice

class MyNewCameraDevice(BaseDevice):
    def __init__(self, device_name):
        super().__init__(device_name)
        self._capabilities = ["feature1", "feature2"]
        
    def initialize(self) -> bool:
        # Implementation
        return True
        
    # Implement other required methods
```

## Migrating from Original PiCamera2

Users familiar with the original PiCamera2 library can easily access the underlying PiCamera2 instance:

```python
from picamera2_restructured import CameraController

camera = CameraController()
camera.initialize()

# Access the original PiCamera2 instance
picam2 = camera.native

# Use original PiCamera2 methods if needed
picam2.capture_file("image.jpg")

camera.close()
```
