"""
CaptureService - Base service for image capture functionality

This module provides the base service class for image capture functionality,
which is extended by specific capture implementations.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
import threading
import os

# Import utilities
from ...utils import ImageUtils, FormatUtils

# Setup logging
logger = logging.getLogger(__name__)


class CaptureService:
    """
    Base service for image capture
    
    This class provides common functionality for all capture services
    and is extended by specific implementations.
    """
    
    def __init__(self, picam2):
        """
        Initialize capture service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        self._picam2 = picam2
        self._lock = threading.RLock()
        self._capture_count = 0
        self._last_capture_time = 0
        
        logger.debug("CaptureService initialized")
    
    def capture(self, **kwargs) -> Any:
        """
        Capture image
        
        Args:
            **kwargs: Capture parameters
            
        Returns:
            Capture result
        """
        with self._lock:
            try:
                self._capture_count += 1
                self._last_capture_time = time.time()
                
                # Override in subclasses
                pass
            except Exception as e:
                logger.error(f"Capture error: {e}")
                return None
    
    def prepare_capture(self, config: Dict[str, Any] = None) -> bool:
        """
        Prepare for capture with optional configuration
        
        Args:
            config: Optional capture configuration
            
        Returns:
            bool: True if prepared successfully
        """
        try:
            if config:
                # Apply temporary configuration for this capture
                self._picam2.configure(config)
                
            return True
        except Exception as e:
            logger.error(f"Failed to prepare capture: {e}")
            return False
    
    def finalize_capture(self, restore_config: Dict[str, Any] = None) -> bool:
        """
        Finalize capture and optionally restore configuration
        
        Args:
            restore_config: Configuration to restore after capture
            
        Returns:
            bool: True if finalized successfully
        """
        try:
            if restore_config:
                # Restore previous configuration
                self._picam2.configure(restore_config)
                
            return True
        except Exception as e:
            logger.error(f"Failed to finalize capture: {e}")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata for the capture
        
        Returns:
            Dict containing metadata
        """
        try:
            metadata = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'capture_count': self._capture_count,
            }
            
            # Add camera info
            if hasattr(self._picam2, 'camera_properties'):
                metadata.update({
                    'camera_model': self._picam2.camera_properties.get('Model', 'Unknown'),
                    'camera_id': self._picam2.camera_properties.get('Location', 'Unknown'),
                })
            
            return metadata
        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            return {}
    
    @property
    def capture_count(self) -> int:
        """Get number of captures performed"""
        return self._capture_count
    
    @property
    def last_capture_time(self) -> float:
        """Get timestamp of last capture"""
        return self._last_capture_time
