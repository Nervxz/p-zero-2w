"""
Device-specific implementations for PiCamera2.

This module contains device-specific implementations for different camera modules
and AI acceleration hardware supported by PiCamera2.
"""

from .device_manager import DeviceManager
from .base_device import BaseDevice

__all__ = [
    'DeviceManager',
    'BaseDevice',
]
