"""
Core implementation modules for PiCamera2.

This module contains the core implementation classes that serve as the foundation
for the higher-level API interfaces.

Note: Most users should not need to interact with these classes directly.
Instead, use the high-level APIs provided in the 'api' module.
"""

from .camera_core import CameraCore
from .configuration_manager import ConfigurationManager

__all__ = [
    'CameraCore',
    'ConfigurationManager',
]
