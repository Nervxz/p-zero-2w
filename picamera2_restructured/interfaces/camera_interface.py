"""
CameraInterface - Interface definition for camera functionality

This module defines the interface that all camera implementations should follow,
ensuring consistent functionality across different camera types.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Union


class CameraInterface(ABC):
    """
    Interface defining required camera functionality
    
    This abstract base class defines the methods that all camera
    implementations should provide.
    """
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the camera
        
        Returns:
            bool: True if initialized successfully
        """
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """
        Start the camera
        
        Returns:
            bool: True if started successfully
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the camera
        
        Returns:
            bool: True if stopped successfully
        """
        pass
    
    @abstractmethod
    def configure(self, config: Dict[str, Any] = None) -> bool:
        """
        Configure the camera with custom settings
        
        Args:
            config: Configuration dictionary
            
        Returns:
            bool: True if configured successfully
        """
        pass
    
    @abstractmethod
    def capture_image(self, format: str = 'jpeg', **kwargs) -> Any:
        """
        Capture an image
        
        Args:
            format: Image format
            **kwargs: Additional capture parameters
            
        Returns:
            Captured image data
        """
        pass
    
    @abstractmethod
    def start_recording(self, output_file: str, **kwargs) -> bool:
        """
        Start video recording
        
        Args:
            output_file: Path to save video file
            **kwargs: Recording parameters
            
        Returns:
            bool: True if recording started successfully
        """
        pass
    
    @abstractmethod
    def stop_recording(self) -> bool:
        """
        Stop video recording
        
        Returns:
            bool: True if recording stopped successfully
        """
        pass
    
    @abstractmethod
    def start_preview(self, **kwargs) -> bool:
        """
        Start camera preview
        
        Args:
            **kwargs: Preview parameters
            
        Returns:
            bool: True if preview started successfully
        """
        pass
    
    @abstractmethod
    def stop_preview(self) -> bool:
        """
        Stop camera preview
        
        Returns:
            bool: True if preview stopped successfully
        """
        pass
    
    @abstractmethod
    def get_camera_info(self) -> Dict[str, Any]:
        """
        Get camera information
        
        Returns:
            Dict with camera information
        """
        pass
    
    @abstractmethod
    def close(self) -> bool:
        """
        Close camera and release resources
        
        Returns:
            bool: True if closed successfully
        """
        pass
