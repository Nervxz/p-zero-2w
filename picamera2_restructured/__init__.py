"""
PiCamera2 Restructured - A modular, easy-to-use API for the PiCamera2 library.

This library reorganizes the PiCamera2 functionality into a modular, accessible structure
similar to the vtol_be-main project. It provides simple interfaces to access camera features
without having to understand the underlying complex codebase.

Key Features:
- Simple, intuitive API interface
- Modular design with clean separation of concerns
- Device-specific optimizations
- Comprehensive capture, preview, and encoding options
- Extensive utility functions

Main modules:
- api: High-level API interfaces for camera usage
- core: Core implementation of camera functionality
- interfaces: Interface definitions and base classes
- devices: Device-specific implementations
- utils: Utility functions and helpers
- services: Service modules for capture, preview, encoding, etc.

For most users, only the api module is needed.

Usage:
    from picamera2_restructured import CameraController
    
    # Initialize camera
    camera = CameraController()
    camera.initialize()
    
    # Capture an image
    img = camera.capture.capture_image()
    
    # Start a preview
    camera.preview.start()
    
    # Close camera
    camera.close()
"""

from .api.camera_controller import CameraController
from .api.capture_api import CaptureAPI
from .api.preview_api import PreviewAPI
from .api.encoding_api import EncodingAPI

__version__ = "0.1.0"
__author__ = "PiCamera2 Team"

__all__ = [
    'CameraController',
    'CaptureAPI',
    'PreviewAPI',
    'EncodingAPI',
]
