"""
Interface definitions for PiCamera2.

This module contains interface definitions and abstract base classes
for the various components of the PiCamera2 library.
"""

from .camera_interface import CameraInterface
from .device_interface import DeviceInterface

__all__ = [
    'CameraInterface',
    'DeviceInterface',
]
