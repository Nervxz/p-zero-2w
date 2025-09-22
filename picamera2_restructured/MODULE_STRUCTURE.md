# PiCamera2 Restructured - Module Structure

This document outlines the complete module structure of the picamera2_restructured library.

```
picamera2_restructured/
│
├── __init__.py                   # Main package initialization
│
├── api/                          # High-level API interfaces
│   ├── __init__.py               # API package initialization
│   ├── camera_controller.py      # Main camera control interface
│   ├── capture_api.py            # Image capture interface
│   ├── preview_api.py            # Camera preview interface
│   ├── encoding_api.py           # Video encoding interface
│   └── README.md                 # API documentation
│
├── core/                         # Core implementation modules
│   ├── __init__.py               # Core package initialization
│   ├── camera_core.py            # Base camera implementation
│   ├── configuration_manager.py  # Camera configuration handling
│   └── README.md                 # Core modules documentation
│
├── devices/                      # Device-specific implementations
│   ├── __init__.py               # Devices package initialization
│   ├── base_device.py            # Base device class
│   ├── device_manager.py         # Device detection and management
│   ├── README.md                 # Devices documentation
│   │
│   ├── imx708/                   # Raspberry Pi Camera Module 3
│   │   ├── __init__.py
│   │   └── imx708_device.py      # IMX708 specific implementation
│   │
│   ├── imx500/                   # Sony IMX500 vision sensor
│   │   ├── __init__.py
│   │   └── imx500_device.py      # IMX500 specific implementation
│   │
│   └── hailo/                    # Hailo AI accelerator
│       ├── __init__.py
│       └── hailo_device.py       # Hailo specific implementation
│
├── interfaces/                   # Interface definitions
│   ├── __init__.py               # Interfaces package initialization
│   ├── camera_interface.py       # Camera interface definition
│   ├── device_interface.py       # Device interface definition
│   └── README.md                 # Interfaces documentation
│
├── services/                     # Service implementations
│   ├── __init__.py               # Services package initialization
│   ├── README.md                 # Services documentation
│   │
│   ├── capture/                  # Image capture services
│   │   ├── __init__.py
│   │   ├── capture_service.py    # Base capture service
│   │   ├── image_capture.py      # Standard image capture
│   │   ├── raw_capture.py        # RAW format capture
│   │   ├── burst_capture.py      # Multi-image burst capture
│   │   └── timelapse_capture.py  # Timelapse capture
│   │
│   ├── preview/                  # Preview services
│   │   ├── __init__.py
│   │   ├── preview_service.py    # Base preview service
│   │   ├── qt_preview.py         # Qt window preview
│   │   ├── drm_preview.py        # DRM direct rendering preview
│   │   └── null_preview.py       # No-display preview
│   │
│   └── encoding/                 # Video encoding services
│       ├── __init__.py
│       ├── encoding_service.py   # Base encoding service
│       ├── h264_encoding.py      # H.264 video encoding
│       ├── mjpeg_encoding.py     # Motion JPEG encoding
│       └── libav_encoding.py     # FFmpeg/LibAV encoding
│
├── utils/                        # Utility functions
│   ├── __init__.py               # Utils package initialization
│   ├── image_utils.py            # Image processing utilities
│   ├── format_utils.py           # Format handling utilities
│   └── README.md                 # Utilities documentation
│
├── examples/                     # Example scripts
│   ├── __init__.py
│   ├── README.md                 # Examples documentation
│   ├── basic_capture.py          # Simple image capture
│   ├── preview_and_capture.py    # Preview with capture
│   ├── video_recording.py        # Video recording
│   ├── timelapse.py              # Timelapse capture
│   ├── advanced_capture.py       # Advanced capture features
│   │
│   └── imx500/                   # IMX500-specific examples
│       ├── __init__.py
│       ├── README.md             # IMX500 examples documentation
│       ├── object_detection_demo.py  # Full object detection demo
│       └── simple_detection.py   # Simple object detection
│
├── README.md                     # Main library documentation
├── QUICKSTART.md                 # Quick start guide
├── USAGE.md                      # Comprehensive usage guide
├── API_REFERENCE.md              # API reference documentation
├── MODULE_STRUCTURE.md           # This file - module structure documentation
└── SUMMARY.md                    # Library structure overview
```

## Module Descriptions

### 1. API Layer (`api/`)
The highest-level interfaces that users directly interact with. These provide simple, intuitive methods for camera operations.

- **camera_controller.py**: Main entry point for all camera operations
- **capture_api.py**: Handles image capture in various formats
- **preview_api.py**: Manages camera preview functionality
- **encoding_api.py**: Controls video recording and encoding

### 2. Core Implementation (`core/`)
The fundamental components that implement core camera functionality.

- **camera_core.py**: Base implementation wrapping the original PiCamera2
- **configuration_manager.py**: Handles camera configuration and settings

### 3. Device Support (`devices/`)
Device-specific implementations for different camera modules and AI accelerators.

- **base_device.py**: Base class for all device implementations
- **device_manager.py**: Detects and initializes camera devices
- **imx708/**: Support for Raspberry Pi Camera Module 3
- **imx500/**: Support for Sony IMX500 intelligent vision sensor
- **hailo/**: Support for Hailo AI accelerators

### 4. Interfaces (`interfaces/`)
Abstract interface definitions that establish the contract for various components.

- **camera_interface.py**: Defines the interface for camera implementations
- **device_interface.py**: Defines the interface for device-specific implementations

### 5. Services (`services/`)
Specialized service implementations for different aspects of camera functionality.

- **capture/**: Services for image capture
- **preview/**: Services for camera preview
- **encoding/**: Services for video encoding

### 6. Utilities (`utils/`)
Helper functions and tools used across the library.

- **image_utils.py**: Image processing utilities
- **format_utils.py**: Format-related utilities

### 7. Examples (`examples/`)
Practical examples showing how to use the library.

- **basic_capture.py**: Simple image capture
- **preview_and_capture.py**: Preview with capture
- **video_recording.py**: Video recording
- **timelapse.py**: Timelapse capture
- **advanced_capture.py**: Advanced features
- **imx500/**: IMX500-specific examples

### 8. Documentation
Comprehensive documentation for the library.

- **README.md**: Main project documentation
- **QUICKSTART.md**: Quick start guide
- **USAGE.md**: Comprehensive usage examples
- **API_REFERENCE.md**: Detailed API reference
- **MODULE_STRUCTURE.md**: This file - module structure documentation
- **SUMMARY.md**: Library structure overview

## Package Hierarchy

The package follows a hierarchical design pattern:
1. Users primarily interact with the **API layer**
2. API classes use **services** for implementation
3. Services use **core** components and **devices**
4. All components can use **utils** for common functionality

This modular structure ensures:
- Clean separation of concerns
- Easy extensibility for new features/devices
- Simplified user experience through high-level APIs
- Access to advanced functionality when needed
