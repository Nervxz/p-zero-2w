"""
BaseDevice - Base class for device-specific implementations

This module provides the base class for device-specific implementations that
can be extended for different camera models and AI acceleration hardware.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

# Setup logging
logger = logging.getLogger(__name__)


class BaseDevice:
    """
    Base class for device-specific implementations
    
    This class provides the common interface for all device-specific implementations
    and should be extended for each supported device.
    """
    
    def __init__(self, name: str, camera_properties: Dict[str, Any] = None):
        """
        Initialize base device
        
        Args:
            name: Device name
            camera_properties: Camera properties dictionary
        """
        self._name = name
        self._camera_properties = camera_properties or {}
        self._capabilities = set()
        self._initialized = False
        
        logger.debug(f"Base device '{name}' initialized")
    
    @property
    def name(self) -> str:
        """Get device name"""
        return self._name
    
    @property
    def camera_properties(self) -> Dict[str, Any]:
        """Get camera properties"""
        return self._camera_properties.copy()
    
    @property
    def capabilities(self) -> List[str]:
        """Get device capabilities"""
        return list(self._capabilities)
    
    def has_capability(self, capability: str) -> bool:
        """
        Check if device has specific capability
        
        Args:
            capability: Capability name
            
        Returns:
            bool: True if device has capability
        """
        return capability in self._capabilities
    
    def initialize(self) -> bool:
        """
        Initialize device
        
        Returns:
            bool: True if device initialized successfully
        """
        self._initialized = True
        return True
    
    def release(self) -> bool:
        """
        Release device resources
        
        Returns:
            bool: True if device released successfully
        """
        self._initialized = False
        return True
    
    def get_recommended_configuration(self) -> Dict[str, Any]:
        """
        Get recommended configuration for this device
        
        Returns:
            Dict containing recommended camera configuration
        """
        # Default configuration - override in device-specific implementations
        return {}
