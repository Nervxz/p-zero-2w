"""
QtPreview - Qt-based camera preview service

This module provides functionality for displaying camera preview
in a Qt window.
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


class QtPreview(PreviewService):
    """
    Qt-based preview service
    
    This class provides functionality for displaying camera preview
    in a Qt window.
    """
    
    def __init__(self, picam2):
        """
        Initialize Qt preview service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        super().__init__(picam2)
        logger.debug("QtPreview service initialized")
    
    def start_preview(self, width: int = 640, height: int = 480, 
                    x: int = 100, y: int = 100,
                    window_title: str = "Camera Preview", 
                    fullscreen: bool = False, **kwargs) -> bool:
        """
        Start Qt preview
        
        Args:
            width: Window width
            height: Window height
            x: Window X position
            y: Window Y position
            window_title: Window title
            fullscreen: Enable fullscreen mode
            **kwargs: Additional preview parameters
            
        Returns:
            bool: True if preview started successfully
        """
        with self._lock:
            if self._preview_active:
                logger.warning("Preview already active")
                return True
            
            try:
                logger.debug(f"Starting Qt preview {width}x{height}")
                
                # Store configuration
                self._preview_config = {
                    'width': width,
                    'height': height,
                    'x': x,
                    'y': y,
                    'window_title': window_title,
                    'fullscreen': fullscreen
                }
                self._preview_config.update(kwargs)
                
                try:
                    # Import Qt preview from picamera2
                    from picamera2.previews import QtPreview
                    
                    # Create Qt preview
                    self._preview_instance = QtPreview(
                        self._picam2,
                        width=width,
                        height=height,
                        x=x,
                        y=y,
                        window_title=window_title
                    )
                    
                    # Apply fullscreen if requested
                    if fullscreen and hasattr(self._preview_instance, 'set_fullscreen'):
                        self._preview_instance.set_fullscreen(True)
                    
                    self._preview_active = True
                    logger.info(f"Qt preview started: {width}x{height}")
                    return True
                    
                except ImportError:
                    logger.error("Failed to import QtPreview - make sure Qt is installed")
                    return False
                
            except Exception as e:
                logger.error(f"Qt preview start error: {e}")
                return False
    
    def stop_preview(self) -> bool:
        """
        Stop Qt preview
        
        Returns:
            bool: True if preview stopped successfully
        """
        with self._lock:
            if not self._preview_active:
                logger.warning("No preview active")
                return True
            
            try:
                logger.debug("Stopping Qt preview")
                
                # Clean up preview instance
                if self._preview_instance:
                    # In a real implementation, we would properly close the Qt window
                    # For now, we'll rely on the picamera2 preview's own cleanup
                    self._preview_instance = None
                
                self._preview_active = False
                logger.info("Qt preview stopped")
                return True
                
            except Exception as e:
                logger.error(f"Qt preview stop error: {e}")
                return False
    
    def update_preview(self, width: int = None, height: int = None, 
                     window_title: str = None, fullscreen: bool = None, **kwargs) -> bool:
        """
        Update Qt preview parameters
        
        Args:
            width: Window width
            height: Window height
            window_title: Window title
            fullscreen: Enable fullscreen mode
            **kwargs: Additional preview parameters
            
        Returns:
            bool: True if preview updated successfully
        """
        with self._lock:
            if not self._preview_active:
                logger.warning("No preview active to update")
                return False
            
            try:
                logger.debug("Updating Qt preview")
                
                # Currently, we need to restart the preview to update parameters
                # Get current config
                current_config = self._preview_config.copy()
                
                # Update with new values
                if width is not None:
                    current_config['width'] = width
                if height is not None:
                    current_config['height'] = height
                if window_title is not None:
                    current_config['window_title'] = window_title
                if fullscreen is not None:
                    current_config['fullscreen'] = fullscreen
                current_config.update(kwargs)
                
                # Stop existing preview
                self.stop_preview()
                
                # Start new preview with updated config
                return self.start_preview(**current_config)
                
            except Exception as e:
                logger.error(f"Qt preview update error: {e}")
                return False
