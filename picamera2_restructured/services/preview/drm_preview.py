"""
DrmPreview - DRM-based camera preview service

This module provides functionality for displaying camera preview
using DRM (Direct Rendering Manager) on Linux.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
import threading
import os

# Import base service
from .preview_service import PreviewService

# Setup logging
logger = logging.getLogger(__name__)


class DrmPreview(PreviewService):
    """
    DRM-based preview service
    
    This class provides functionality for displaying camera preview
    using DRM (Direct Rendering Manager) on Linux.
    """
    
    def __init__(self, picam2):
        """
        Initialize DRM preview service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        super().__init__(picam2)
        logger.debug("DrmPreview service initialized")
    
    def start_preview(self, width: int = None, height: int = None, **kwargs) -> bool:
        """
        Start DRM preview
        
        Args:
            width: Optional width override
            height: Optional height override
            **kwargs: Additional preview parameters
            
        Returns:
            bool: True if preview started successfully
        """
        with self._lock:
            if self._preview_active:
                logger.warning("Preview already active")
                return True
            
            try:
                logger.debug(f"Starting DRM preview")
                
                # Store configuration
                self._preview_config = {
                    'width': width,
                    'height': height
                }
                self._preview_config.update(kwargs)
                
                try:
                    # Import DRM preview from picamera2
                    from picamera2.previews import DrmPreview
                    
                    # Create DRM preview
                    preview_args = {}
                    if width is not None and height is not None:
                        preview_args['width'] = width
                        preview_args['height'] = height
                    
                    self._preview_instance = DrmPreview(self._picam2, **preview_args)
                    
                    self._preview_active = True
                    logger.info("DRM preview started")
                    return True
                    
                except ImportError:
                    logger.error("Failed to import DrmPreview - make sure DRM is supported on your system")
                    return False
                
            except Exception as e:
                logger.error(f"DRM preview start error: {e}")
                return False
    
    def stop_preview(self) -> bool:
        """
        Stop DRM preview
        
        Returns:
            bool: True if preview stopped successfully
        """
        with self._lock:
            if not self._preview_active:
                logger.warning("No preview active")
                return True
            
            try:
                logger.debug("Stopping DRM preview")
                
                # Clean up preview instance
                if self._preview_instance:
                    # In a real implementation, we would properly close the DRM preview
                    # For now, we'll rely on the picamera2 preview's own cleanup
                    self._preview_instance = None
                
                self._preview_active = False
                logger.info("DRM preview stopped")
                return True
                
            except Exception as e:
                logger.error(f"DRM preview stop error: {e}")
                return False
    
    def is_drm_supported(self) -> bool:
        """
        Check if DRM is supported on the system
        
        Returns:
            bool: True if DRM is supported
        """
        try:
            import importlib.util
            drm_available = importlib.util.find_spec("picamera2.previews.drm_preview") is not None
            return drm_available
        except:
            return False
