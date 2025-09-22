"""
CameraController - High-level Python API for PiCamera2

This module provides a simplified, high-level interface for camera operations
built on top of the comprehensive PiCamera2 library.

Features:
- Easy camera initialization and configuration
- Simplified capture interface
- Real-time data access
- Event-driven monitoring
- Configuration management
- Preview control

Usage:
    from picamera2_restructured import CameraController
    
    # Simple usage
    camera = CameraController()
    camera.initialize()
    
    # Capture an image
    img = camera.capture.capture_image()
    
    # Start a preview
    camera.preview.start()
    
    # Record video
    camera.encoding.start_video_recording("video.mp4")
    time.sleep(5)
    camera.encoding.stop_video_recording()
    
    # Close camera
    camera.close()
    
    # Context manager usage  
    with CameraController() as camera:
        # Your operations here
        pass
"""

from ..core import CameraCore, ConfigurationManager
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple

# Import original PiCamera2 functionality
from picamera2.picamera2 import Picamera2

# Import our API classes
from .capture_api import CaptureAPI
from .preview_api import PreviewAPI
from .encoding_api import EncodingAPI

# Setup logging
logger = logging.getLogger(__name__)


class CameraController:
    """
    High-level camera controller interface
    Provides a simplified API for common camera operations
    """
    
    def __init__(self, camera_num: int = 0):
        """
        Initialize camera controller
        
        Args:
            camera_num: Camera number to use (default: 0 for main camera)
        """
        self._camera_num = camera_num
        self._picam2 = None
        self._initialized = False
        
        # API components
        self._capture_api = None
        self._preview_api = None
        self._encoding_api = None
        
        # Cache for camera data
        self._camera_info = {}
        self._camera_config = {}
        
        logger.info("CameraController created")
    
    def initialize(self) -> bool:
        """
        Initialize the camera
        
        Returns:
            bool: True if initialized successfully
        """
        if self._initialized:
            logger.warning("Camera already initialized")
            return True
        
        try:
            logger.info(f"Initializing camera {self._camera_num}...")
            self._picam2 = Picamera2(camera_num=self._camera_num)
            
            # Initialize API components
            self._capture_api = CaptureAPI(self._picam2)
            self._preview_api = PreviewAPI(self._picam2)
            self._encoding_api = EncodingAPI(self._picam2)
            
            # Get camera information
            self._camera_info = self._get_camera_info()
            
            # Configure with defaults
            self._configure_default()
            
            self._initialized = True
            logger.info("Camera initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self._initialized = False
            return False
    
    def _configure_default(self):
        """Set up default camera configuration"""
        try:
            # Create a default configuration
            self._picam2.configure()
            logger.info("Default configuration applied")
        except Exception as e:
            logger.error(f"Failed to apply default configuration: {e}")
    
    def _get_camera_info(self) -> Dict[str, Any]:
        """Get camera information"""
        if not self._picam2:
            return {}
        
        try:
            info = {
                'id': self._camera_num,
                'camera_name': self._picam2.camera_properties.get('Model', 'Unknown'),
                'resolution': self._get_max_resolution(),
                'sensor': self._picam2.camera_properties.get('Location', 'Unknown'),
                'properties': self._picam2.camera_properties
            }
            return info
        except Exception as e:
            logger.error(f"Failed to get camera info: {e}")
            return {'error': str(e)}
    
    def _get_max_resolution(self) -> Tuple[int, int]:
        """Get maximum supported resolution"""
        if not self._picam2:
            return (0, 0)
        
        try:
            # Get the largest resolution available
            streams = self._picam2.camera_config['main'].size
            return streams
        except:
            try:
                # Try to get from camera properties
                return (
                    self._picam2.camera_properties.get('PixelArraySize', (0, 0))[0],
                    self._picam2.camera_properties.get('PixelArraySize', (0, 0))[1]
                )
            except:
                return (0, 0)
    
    @property
    def camera_info(self) -> Dict[str, Any]:
        """Get camera information"""
        return self._camera_info
    
    @property
    def is_initialized(self) -> bool:
        """Check if camera is initialized"""
        return self._initialized
    
    @property
    def capture(self) -> CaptureAPI:
        """Access the capture API"""
        if not self._initialized:
            self.initialize()
        return self._capture_api
    
    @property
    def preview(self) -> PreviewAPI:
        """Access the preview API"""
        if not self._initialized:
            self.initialize()
        return self._preview_api
    
    @property
    def encoding(self) -> EncodingAPI:
        """Access the encoding API"""
        if not self._initialized:
            self.initialize()
        return self._encoding_api
    
    @property
    def native(self) -> Picamera2:
        """Access the underlying Picamera2 instance for advanced usage"""
        if not self._initialized:
            self.initialize()
        return self._picam2
    
    def configure(self, config: Dict[str, Any] = None) -> bool:
        """
        Configure the camera with custom settings
        
        Args:
            config: Configuration dictionary
            
        Returns:
            bool: True if configured successfully
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            if config:
                # Custom configuration
                self._picam2.configure(config)
            else:
                # Default configuration
                self._configure_default()
            
            return True
        except Exception as e:
            logger.error(f"Failed to configure camera: {e}")
            return False
    
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
            self._picam2.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            return False
    
    def stop(self):
        """Stop the camera"""
        if self._picam2 and self._initialized:
            try:
                self._picam2.stop()
                logger.info("Camera stopped")
            except Exception as e:
                logger.error(f"Error stopping camera: {e}")
    
    def close(self):
        """Close the camera and release resources"""
        self.stop()
        
        if self._picam2 and self._initialized:
            try:
                self._picam2.close()
                logger.info("Camera closed and resources released")
            except Exception as e:
                logger.error(f"Error closing camera: {e}")
        
        self._picam2 = None
        self._initialized = False
    
    def get_controls(self) -> Dict[str, Any]:
        """
        Get all available camera controls
        
        Returns:
            Dict[str, Any]: Dictionary of camera controls
        """
        if not self._initialized:
            if not self.initialize():
                return {}
        
        try:
            return self._picam2.camera_controls
        except Exception as e:
            logger.error(f"Failed to get camera controls: {e}")
            return {}
    
    def set_control(self, control: str, value: Any) -> bool:
        """
        Set camera control value
        
        Args:
            control: Control name
            value: Control value
            
        Returns:
            bool: True if set successfully
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            controls = {control: value}
            self._picam2.set_controls(controls)
            return True
        except Exception as e:
            logger.error(f"Failed to set camera control {control}: {e}")
            return False
    
    def get_all_data(self) -> Dict[str, Any]:
        """
        Get all camera data
        
        Returns:
            Dict[str, Any]: Dictionary with all camera data
        """
        if not self._initialized:
            if not self.initialize():
                return {"error": "Camera not initialized"}
        
        return {
            "camera_info": self.camera_info,
            "controls": self.get_controls(),
            "status": "running" if self._picam2 and self._picam2.started else "stopped",
        }
    
    def get_all_data_json(self) -> str:
        """
        Get all camera data in JSON format
        
        Returns:
            str: JSON string with all camera data
        """
        import json
        return json.dumps(self.get_all_data(), indent=2, default=str)
    
    # Context manager support
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
