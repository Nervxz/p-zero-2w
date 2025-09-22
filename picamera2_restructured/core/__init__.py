"""
Core implementation modules for PiCamera2.

This module contains the core implementation classes that serve as the foundation
for the higher-level API interfaces.

Note: Most users should not need to interact with these classes directly.
Instead, use the high-level APIs provided in the 'api' module.

This module uses lazy loading to improve startup time and reduce memory usage.
"""

# Import lazy loading utilities
from .lazy_loader import lazy_import, LazyObject
from .module_registry import (
    register_module, get_module, initialize_module, initialize_all_modules,
    ModuleLoader, module_loader, module_registry
)

# Register core modules
register_module('camera_core', 'picamera2_restructured.core.camera_core')
register_module('config_manager', 'picamera2_restructured.core.configuration_manager')

# Define lazy imports
_camera_core = lazy_import('.camera_core', __package__)
_config_manager = lazy_import('.configuration_manager', __package__)

# Create lazy objects for commonly used classes
CameraCore = LazyObject(lambda: _camera_core.CameraCore)
ConfigurationManager = LazyObject(lambda: _config_manager.ConfigurationManager)

# For backward compatibility, ensure direct imports still work
from .camera_core import CameraCore
from .configuration_manager import ConfigurationManager

__all__ = [
    # Core classes
    'CameraCore',
    'ConfigurationManager',
    
    # Lazy loading utilities
    'lazy_import',
    'LazyObject',
    
    # Module registry utilities
    'register_module',
    'get_module',
    'initialize_module',
    'initialize_all_modules',
    'ModuleLoader',
    'module_loader',
    'module_registry',
]
