"""
CameraCore - Core camera implementation and initialization

This module provides the low-level camera core functionality that forms the foundation
for the high-level API interfaces. It handles camera initialization, resource management,
and provides access to the underlying Picamera2 instance.

Note: This module is primarily for internal use by the API classes and not intended
to be used directly by most users.
"""

import logging
import threading
from typing import Dict, Any, Optional, List, Tuple

# Import original PiCamera2 functionality
from picamera2.picamera2 import Picamera2

# Setup logging
logger = logging.getLogger(__name__)


class CameraCore:
    """
    Core camera implementation class
    
    This class serves as a wrapper around the Picamera2 class and provides
    common functionality for the higher-level API interfaces.
    """
    
    def __init__(self, camera_num: int = 0):
        """
        Initialize camera core
        
        Args:
            camera_num: Camera number to use (default: 0 for main camera)
        """
        self._camera_num = camera_num
        self._picam2: Optional[Picamera2] = None
        self._initialized = False
        self._lock = threading.RLock()
        
        logger.debug(f"CameraCore initialized for camera {camera_num}")
    
    def initialize(self) -> bool:
        """
        Initialize the camera hardware
        
        Returns:
            bool: True if camera initialized successfully
        """
        if self._initialized:
            logger.debug("Camera already initialized")
            return True
        
        try:
            with self._lock:
                logger.debug(f"Initializing camera {self._camera_num}")
                self._picam2 = Picamera2(camera_num=self._camera_num)
                self._initialized = True
                return True
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self._initialized = False
            return False
    
    @property
    def picam2(self) -> Optional[Picamera2]:
        """
        Get the underlying Picamera2 instance
        
        Returns:
            Picamera2 instance or None if not initialized
        """
        return self._picam2
    
    @property
    def camera_num(self) -> int:
        """Get the camera number"""
        return self._camera_num
    
    @property
    def is_initialized(self) -> bool:
        """Check if camera is initialized"""
        return self._initialized
    
    def start(self) -> bool:
        """
        Start the camera
        
        Returns:
            bool: True if started successfully
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            with self._lock:
                self._picam2.start()
                return True
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop the camera
        
        Returns:
            bool: True if stopped successfully
        """
        if not self._initialized or not self._picam2:
            return True
        
        try:
            with self._lock:
                if self._picam2.started:
                    self._picam2.stop()
                return True
        except Exception as e:
            logger.error(f"Failed to stop camera: {e}")
            return False
    
    def close(self) -> bool:
        """
        Close the camera and release resources
        
        Returns:
            bool: True if closed successfully
        """
        if not self._initialized or not self._picam2:
            return True
        
        try:
            with self._lock:
                if self._picam2.started:
                    self._picam2.stop()
                self._picam2.close()
                self._initialized = False
                self._picam2 = None
                return True
        except Exception as e:
            logger.error(f"Failed to close camera: {e}")
            return False
    
    def get_camera_info(self) -> Dict[str, Any]:
        """
        Get camera information
        
        Returns:
            Dict with camera information
        """
        if not self._initialized or not self._picam2:
            return {}
        
        try:
            properties = self._picam2.camera_properties
            info = {
                'id': self._camera_num,
                'name': properties.get('Model', 'Unknown'),
                'location': properties.get('Location', 'Unknown'),
                'pixel_array_size': properties.get('PixelArraySize', (0, 0)),
                'color_filter_arrangement': properties.get('ColorFilterArrangement', 'Unknown'),
                'raw_formats': properties.get('raw_formats', []),
            }
            
            return info
        except Exception as e:
            logger.error(f"Failed to get camera info: {e}")
            return {'error': str(e)}
    
    def get_camera_modes(self) -> List[Dict[str, Any]]:
        """
        Get available camera modes
        
        Returns:
            List of camera modes
        """
        if not self._initialized or not self._picam2:
            return []
        
        try:
            return self._picam2.sensor_modes
        except Exception as e:
            logger.error(f"Failed to get camera modes: {e}")
            return []
    
    def __del__(self):
        """Destructor to ensure resources are released"""
        self.close()
