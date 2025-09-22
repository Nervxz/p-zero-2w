"""
ImageCapture - Standard image capture service

This module provides functionality for capturing standard images
in various formats (JPEG, PNG, etc.).
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union, BinaryIO
import threading
import os
import io
import numpy as np
from PIL import Image

# Import base service
from .capture_service import CaptureService

# Import utilities
from ...utils import ImageUtils, FormatUtils

# Setup logging
logger = logging.getLogger(__name__)


class ImageCapture(CaptureService):
    """
    Standard image capture service
    
    This class provides functionality for capturing standard images
    in various formats.
    """
    
    def __init__(self, picam2):
        """
        Initialize image capture service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        super().__init__(picam2)
        
        # Default capture parameters
        self._default_format = 'jpeg'
        self._default_quality = 95
        
        logger.debug("ImageCapture service initialized")
    
    def capture(self, format: str = None, quality: int = None, **kwargs) -> Union[bytes, np.ndarray]:
        """
        Capture image
        
        Args:
            format: Image format ('jpeg', 'png', 'array', etc.)
            quality: Image quality for JPEG (0-100)
            **kwargs: Additional capture parameters
            
        Returns:
            Image data as bytes or numpy array
        """
        with self._lock:
            try:
                # Call parent method for tracking
                super().capture()
                
                # Set defaults
                format = format or self._default_format
                quality = quality or self._default_quality
                
                # Select capture method based on format
                if format.lower() in ('jpeg', 'jpg'):
                    return self.capture_jpeg(quality=quality, **kwargs)
                elif format.lower() == 'png':
                    return self.capture_png(**kwargs)
                elif format.lower() == 'array':
                    return self.capture_array(**kwargs)
                else:
                    logger.warning(f"Unsupported format: {format}, using JPEG")
                    return self.capture_jpeg(quality=quality, **kwargs)
                
            except Exception as e:
                logger.error(f"Capture error: {e}")
                return None
    
    def capture_jpeg(self, quality: int = 95, **kwargs) -> bytes:
        """
        Capture JPEG image
        
        Args:
            quality: JPEG quality (0-100)
            **kwargs: Additional capture parameters
            
        Returns:
            JPEG image data as bytes
        """
        try:
            logger.debug(f"Capturing JPEG with quality {quality}")
            
            # Capture as array first
            array = self._picam2.capture_array()
            
            # Convert to JPEG
            return ImageUtils.array_to_jpeg(array, quality)
            
        except Exception as e:
            logger.error(f"JPEG capture error: {e}")
            return bytes()
    
    def capture_png(self, **kwargs) -> bytes:
        """
        Capture PNG image
        
        Args:
            **kwargs: Additional capture parameters
            
        Returns:
            PNG image data as bytes
        """
        try:
            logger.debug("Capturing PNG")
            
            # Capture as array first
            array = self._picam2.capture_array()
            
            # Convert to PNG
            return ImageUtils.array_to_png(array)
            
        except Exception as e:
            logger.error(f"PNG capture error: {e}")
            return bytes()
    
    def capture_array(self, **kwargs) -> np.ndarray:
        """
        Capture image as numpy array
        
        Args:
            **kwargs: Additional capture parameters
            
        Returns:
            Image data as numpy array
        """
        try:
            logger.debug("Capturing array")
            
            # Direct array capture
            return self._picam2.capture_array()
            
        except Exception as e:
            logger.error(f"Array capture error: {e}")
            return np.array([])
    
    def capture_file(self, file_path: str, format: str = None, quality: int = 95, **kwargs) -> bool:
        """
        Capture image directly to file
        
        Args:
            file_path: Path to save the image
            format: Image format (if None, determined from file extension)
            quality: JPEG quality (0-100)
            **kwargs: Additional capture parameters
            
        Returns:
            bool: True if captured successfully
        """
        try:
            logger.debug(f"Capturing to file: {file_path}")
            
            # Determine format from file extension if not specified
            if format is None:
                format = FormatUtils.guess_file_format(file_path)
            
            # Capture image data
            image_data = self.capture(format=format, quality=quality, **kwargs)
            
            if image_data is None:
                return False
                
            # Save to file
            if isinstance(image_data, bytes):
                with open(file_path, 'wb') as f:
                    f.write(image_data)
            else:
                # Handle numpy array
                img = Image.fromarray(image_data)
                img.save(file_path)
            
            return True
            
        except Exception as e:
            logger.error(f"File capture error: {e}")
            return False
    
    def capture_with_timestamp(self, format: str = 'jpeg', position: str = 'bottom-right', 
                             time_format: str = '%Y-%m-%d %H:%M:%S', **kwargs) -> Union[bytes, np.ndarray]:
        """
        Capture image with timestamp overlay
        
        Args:
            format: Image format
            position: Timestamp position ('top-left', 'top-right', 'bottom-left', 'bottom-right')
            time_format: Time format string
            **kwargs: Additional capture parameters
            
        Returns:
            Image data with timestamp
        """
        try:
            # Capture image
            image = self.capture(format='array', **kwargs)
            
            if image is None:
                return None
                
            # Add timestamp
            timestamped = ImageUtils.add_timestamp(image, format_str=time_format, position=position)
            
            # Convert to requested format
            if format.lower() in ('jpeg', 'jpg'):
                quality = kwargs.get('quality', 95)
                return ImageUtils.array_to_jpeg(timestamped, quality)
            elif format.lower() == 'png':
                return ImageUtils.array_to_png(timestamped)
            else:
                return timestamped
                
        except Exception as e:
            logger.error(f"Timestamp capture error: {e}")
            return None
