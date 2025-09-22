# PiCamera2 Interfaces Module

This module contains interface definitions and abstract base classes that establish the contract for various components in the library.

## Overview

The interfaces module defines the formal contracts that different implementations must follow, ensuring consistency across the library and enabling interchangeable components.

## Key Interfaces

### CameraInterface

Defines the required interface for camera implementations:

```python
from picamera2_restructured.interfaces import CameraInterface

# Abstract class - not instantiated directly
# Used to define the contract that camera implementations must follow
class MyCameraImplementation(CameraInterface):
    def initialize(self) -> bool:
        # Implementation required
        pass
    
    def capture_image(self, format: str = 'jpeg', **kwargs) -> Any:
        # Implementation required
        pass
    
    # All other interface methods must be implemented
```

### DeviceInterface

Defines the required interface for device-specific implementations:

```python
from picamera2_restructured.interfaces import DeviceInterface

# Abstract class - not instantiated directly
# Used to define the contract that device implementations must follow
class MyDeviceImplementation(DeviceInterface):
    @property
    def capabilities(self) -> List[str]:
        # Implementation required
        return ["feature1", "feature2"]
    
    def initialize(self) -> bool:
        # Implementation required
        pass
    
    # All other interface methods must be implemented
```

## Purpose

These interfaces ensure that:

1. All implementations provide a consistent set of methods
2. Different implementations can be swapped without changing client code
3. New implementations can be added while maintaining compatibility
4. Code is more maintainable through clear contracts

The interfaces module is primarily used by developers extending the library with new implementations, not by end users.
