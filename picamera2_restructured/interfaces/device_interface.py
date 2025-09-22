"""
DeviceInterface - Interface definition for device functionality

This module defines the interface that all device implementations should follow,
ensuring consistent functionality across different device types.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Union, Set


class DeviceInterface(ABC):
    """
    Interface defining required device functionality
    
    This abstract base class defines the methods that all device
    implementations should provide.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get device name"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """Get device capabilities"""
        pass
    
    @abstractmethod
    def has_capability(self, capability: str) -> bool:
        """
        Check if device has specific capability
        
        Args:
            capability: Capability name
            
        Returns:
            bool: True if device has capability
        """
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize device
        
        Returns:
            bool: True if device initialized successfully
        """
        pass
    
    @abstractmethod
    def release(self) -> bool:
        """
        Release device resources
        
        Returns:
            bool: True if device released successfully
        """
        pass
    
    @abstractmethod
    def get_recommended_configuration(self) -> Dict[str, Any]:
        """
        Get recommended configuration for this device
        
        Returns:
            Dict containing recommended camera configuration
        """
        pass
