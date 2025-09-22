"""
RawCapture - RAW image capture service

This module provides functionality for capturing RAW format images,
which contain unprocessed sensor data.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
import threading
import os
import numpy as np
import io

# Import base service
from .capture_service import CaptureService

# Setup logging
logger = logging.getLogger(__name__)


class RawCapture(CaptureService):
    """
    RAW image capture service
    
    This class provides functionality for capturing RAW format images,
    which contain unprocessed sensor data.
    """
    
    def __init__(self, picam2):
        """
        Initialize RAW capture service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        super().__init__(picam2)
        logger.debug("RawCapture service initialized")
    
    def capture(self, **kwargs) -> np.ndarray:
        """
        Capture RAW image
        
        Args:
            **kwargs: Additional capture parameters
            
        Returns:
            RAW image data as numpy array
        """
        with self._lock:
            try:
                # Call parent method for tracking
                super().capture()
                
                logger.debug("Capturing RAW image")
                
                # Capture RAW image
                return self._picam2.capture_array("raw")
                
            except Exception as e:
                logger.error(f"RAW capture error: {e}")
                return None
    
    def capture_dng(self, **kwargs) -> bytes:
        """
        Capture DNG format image
        
        Args:
            **kwargs: Additional capture parameters
            
        Returns:
            DNG image data as bytes
        """
        with self._lock:
            try:
                logger.debug("Capturing DNG image")
                
                # Use request to get DNG data
                request = self._picam2.capture_request()
                
                # Currently, directly returning raw array as we don't have DNG conversion
                # In a real implementation, this would convert the raw data to DNG format
                raw_array = request.make_array("raw")
                
                # Release request
                request.release()
                
                # As a placeholder, we're just returning the raw array
                # In reality, we would convert this to DNG format
                logger.warning("DNG conversion not implemented, returning raw array")
                return raw_array
                
            except Exception as e:
                logger.error(f"DNG capture error: {e}")
                return None
    
    def capture_file(self, file_path: str, format: str = 'raw', **kwargs) -> bool:
        """
        Capture RAW image directly to file
        
        Args:
            file_path: Path to save the image
            format: Image format ('raw' or 'dng')
            **kwargs: Additional capture parameters
            
        Returns:
            bool: True if captured successfully
        """
        try:
            logger.debug(f"Capturing RAW to file: {file_path}")
            
            if format.lower() == 'dng':
                # Capture DNG
                dng_data = self.capture_dng(**kwargs)
                
                if dng_data is None:
                    return False
                
                # Save to file (in a real implementation, this would be DNG data)
                # For now, we're just saving the array
                np.save(file_path, dng_data)
                
            else:
                # Capture raw array
                raw_data = self.capture(**kwargs)
                
                if raw_data is None:
                    return False
                
                # Save raw array
                np.save(file_path, raw_data)
            
            return True
            
        except Exception as e:
            logger.error(f"RAW file capture error: {e}")
            return False
    
    def capture_with_metadata(self, **kwargs) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Capture RAW image with metadata
        
        Args:
            **kwargs: Additional capture parameters
            
        Returns:
            Tuple of (RAW image data, metadata)
        """
        try:
            logger.debug("Capturing RAW with metadata")
            
            # Use request to get both raw data and metadata
            request = self._picam2.capture_request()
            
            # Extract raw data
            raw_data = request.make_array("raw")
            
            # Extract metadata
            metadata = request.get_metadata()
            
            # Release request
            request.release()
            
            return raw_data, metadata
            
        except Exception as e:
            logger.error(f"RAW capture with metadata error: {e}")
            return None, {}
    
    def is_raw_supported(self) -> bool:
        """
        Check if RAW capture is supported by the camera
        
        Returns:
            bool: True if RAW is supported
        """
        try:
            # Check if raw format is available in camera properties
            if hasattr(self._picam2, 'camera_properties'):
                raw_formats = self._picam2.camera_properties.get('raw_formats', [])
                return len(raw_formats) > 0
            
            return False
        except Exception as e:
            logger.error(f"Error checking RAW support: {e}")
            return False
