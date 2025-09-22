"""
CaptureAPI - Simplified interface for capturing images and metadata

This module provides easy-to-use methods for capturing images in different formats,
capturing multiple images, and handling image metadata.

Usage:
    from picamera2_restructured import CameraController
    
    camera = CameraController()
    camera.initialize()
    
    # Capture a JPEG image
    jpeg_image = camera.capture.capture_image()
    
    # Capture a raw image
    raw_image = camera.capture.capture_raw()
    
    # Capture with custom settings
    custom_image = camera.capture.capture_image(format='png', config={'main': {'size': (1920, 1080)}})
    
    # Capture multiple images
    images = camera.capture.capture_burst(count=5)
    
    # Capture image with metadata
    image, metadata = camera.capture.capture_with_metadata()
"""

from ..utils import ImageUtils
import time
import logging
import io
from typing import Dict, Any, Optional, List, Tuple, Union
import numpy as np
from PIL import Image

# Setup logging
logger = logging.getLogger(__name__)


class CaptureAPI:
    """
    High-level capture API for PiCamera2
    Provides simplified methods for image capture
    """
    
    def __init__(self, picam2):
        """
        Initialize capture API
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        self._picam2 = picam2
    
    def capture_image(self, format: str = 'jpeg', config: Dict = None) -> Union[np.ndarray, bytes]:
        """
        Capture a single image
        
        Args:
            format: Image format ('jpeg', 'png', 'raw', etc.)
            config: Optional configuration for this capture
            
        Returns:
            Image data as numpy array or bytes
        """
        try:
            logger.info(f"Capturing {format} image")
            
            # Handle format-specific captures
            if format.lower() == 'jpeg':
                return self._capture_jpeg()
            elif format.lower() == 'png':
                return self._capture_png()
            elif format.lower() == 'raw':
                return self.capture_raw()
            else:
                # Default to numpy array for other formats
                return self._picam2.capture_array()
                
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return None
    
    def _capture_jpeg(self) -> bytes:
        """Capture a JPEG image"""
        try:
            # Capture as array first
            array = self._picam2.capture_array()
            
            # Convert to JPEG
            img = Image.fromarray(array)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Error capturing JPEG: {e}")
            return bytes()
    
    def _capture_png(self) -> bytes:
        """Capture a PNG image"""
        try:
            # Capture as array first
            array = self._picam2.capture_array()
            
            # Convert to PNG
            img = Image.fromarray(array)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Error capturing PNG: {e}")
            return bytes()
    
    def capture_raw(self) -> np.ndarray:
        """
        Capture a raw image
        
        Returns:
            Raw image data as numpy array
        """
        try:
            logger.info("Capturing raw image")
            return self._picam2.capture_array("raw")
        except Exception as e:
            logger.error(f"Error capturing raw image: {e}")
            return None
    
    def capture_with_metadata(self, format: str = 'jpeg') -> Tuple[Union[np.ndarray, bytes], Dict[str, Any]]:
        """
        Capture an image with metadata
        
        Args:
            format: Image format ('jpeg', 'png', 'raw', etc.)
            
        Returns:
            Tuple of (image data, metadata)
        """
        try:
            logger.info(f"Capturing {format} image with metadata")
            
            # Capture request with metadata
            request = self._picam2.capture_request()
            
            # Extract image based on format
            if format.lower() == 'jpeg':
                img_data = request.make_buffer("main")
            elif format.lower() == 'raw':
                img_data = request.make_array("raw")
            else:
                img_data = request.make_array("main")
            
            # Extract metadata
            metadata = request.get_metadata()
            
            # Release request
            request.release()
            
            return img_data, metadata
            
        except Exception as e:
            logger.error(f"Error capturing image with metadata: {e}")
            return None, {}
    
    def capture_burst(self, count: int = 5, interval: float = 0.0, format: str = 'jpeg') -> List[Union[np.ndarray, bytes]]:
        """
        Capture a burst of images
        
        Args:
            count: Number of images to capture
            interval: Time interval between captures (seconds)
            format: Image format
            
        Returns:
            List of captured images
        """
        images = []
        
        try:
            logger.info(f"Capturing burst of {count} images")
            
            for i in range(count):
                images.append(self.capture_image(format))
                if i < count - 1 and interval > 0:
                    time.sleep(interval)
            
            return images
            
        except Exception as e:
            logger.error(f"Error during burst capture: {e}")
            return images
    
    def capture_to_file(self, file_path: str, format: str = 'jpeg') -> bool:
        """
        Capture an image directly to file
        
        Args:
            file_path: Path to save the file
            format: Image format
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Capturing image to file: {file_path}")
            
            image = self.capture_image(format)
            
            if image is not None:
                if isinstance(image, bytes):
                    # Save bytes directly
                    with open(file_path, 'wb') as f:
                        f.write(image)
                else:
                    # Save numpy array
                    img = Image.fromarray(image)
                    img.save(file_path)
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error capturing to file: {e}")
            return False
    
    def capture_continuous(self, count: int, interval: float = 1.0, callback=None) -> List[np.ndarray]:
        """
        Continuously capture images with callback
        
        Args:
            count: Number of images to capture
            interval: Time interval between captures (seconds)
            callback: Function to call for each image
            
        Returns:
            List of captured images (if no callback)
        """
        images = []
        
        try:
            logger.info(f"Starting continuous capture for {count} images")
            
            for i in range(count):
                img = self._picam2.capture_array()
                
                if callback:
                    # Call the callback with the image
                    callback(img, i)
                else:
                    # Store the image
                    images.append(img)
                
                if i < count - 1:
                    time.sleep(interval)
            
            return images
            
        except Exception as e:
            logger.error(f"Error during continuous capture: {e}")
            return images
    
    def configure_capture(self, config: Dict[str, Any]) -> bool:
        """
        Configure capture settings
        
        Args:
            config: Capture configuration
            
        Returns:
            bool: True if configured successfully
        """
        try:
            self._picam2.configure(config)
            return True
        except Exception as e:
            logger.error(f"Error configuring capture: {e}")
            return False
