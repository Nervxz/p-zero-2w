"""
PreviewAPI - Simplified interface for camera preview functionality

This module provides easy-to-use methods for controlling camera previews,
including starting, stopping, and configuring different preview methods.

Usage:
    from picamera2_restructured import CameraController
    
    camera = CameraController()
    camera.initialize()
    
    # Start a preview
    camera.preview.start()
    
    # Start a Qt preview window
    camera.preview.start_qt()
    
    # Configure preview settings
    camera.preview.configure(width=800, height=600)
    
    # Stop preview
    camera.preview.stop()
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple, Union

# Setup logging
logger = logging.getLogger(__name__)


class PreviewAPI:
    """
    High-level preview API for PiCamera2
    Provides simplified methods for camera preview
    """
    
    def __init__(self, picam2):
        """
        Initialize preview API
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        self._picam2 = picam2
        self._preview_active = False
        self._preview_type = None
        self._preview_config = {}
    
    def start(self, preview_type: str = "default", **kwargs) -> bool:
        """
        Start camera preview
        
        Args:
            preview_type: Type of preview ('default', 'qt', 'null', 'drm')
            **kwargs: Additional preview parameters
            
        Returns:
            bool: True if preview started successfully
        """
        try:
            logger.info(f"Starting {preview_type} preview")
            
            # Stop any existing preview
            if self._preview_active:
                self.stop()
            
            # Select preview based on type
            if preview_type.lower() == "qt":
                return self.start_qt(**kwargs)
            elif preview_type.lower() == "null":
                return self.start_null(**kwargs)
            elif preview_type.lower() == "drm":
                return self.start_drm(**kwargs)
            else:
                # Default preview
                self._picam2.start_preview(**kwargs)
                self._preview_active = True
                self._preview_type = "default"
                return True
                
        except Exception as e:
            logger.error(f"Error starting preview: {e}")
            return False
    
    def start_qt(self, x: int = 100, y: int = 100, width: int = 640, height: int = 480, window_title: str = "Camera Preview") -> bool:
        """
        Start Qt preview window
        
        Args:
            x: Window X position
            y: Window Y position
            width: Window width
            height: Window height
            window_title: Window title
            
        Returns:
            bool: True if preview started successfully
        """
        try:
            logger.info(f"Starting Qt preview ({width}x{height})")
            
            from picamera2.previews import QtPreview
            
            # Create Qt preview
            preview = QtPreview(
                self._picam2,
                x=x,
                y=y,
                width=width,
                height=height,
                window_title=window_title
            )
            
            # Store configuration
            self._preview_config = {
                'x': x, 'y': y, 
                'width': width, 'height': height,
                'window_title': window_title
            }
            
            self._preview_active = True
            self._preview_type = "qt"
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting Qt preview: {e}")
            return False
    
    def start_null(self) -> bool:
        """
        Start null preview (no visible output)
        
        Returns:
            bool: True if null preview started successfully
        """
        try:
            logger.info("Starting null preview")
            
            from picamera2.previews import NullPreview
            
            # Create null preview
            preview = NullPreview(self._picam2)
            
            self._preview_active = True
            self._preview_type = "null"
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting null preview: {e}")
            return False
    
    def start_drm(self) -> bool:
        """
        Start DRM preview (direct rendering)
        
        Returns:
            bool: True if DRM preview started successfully
        """
        try:
            logger.info("Starting DRM preview")
            
            from picamera2.previews import DrmPreview
            
            # Create DRM preview
            preview = DrmPreview(self._picam2)
            
            self._preview_active = True
            self._preview_type = "drm"
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting DRM preview: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop active preview
        
        Returns:
            bool: True if preview stopped successfully
        """
        if not self._preview_active:
            return True
        
        try:
            logger.info("Stopping preview")
            
            self._picam2.stop_preview()
            self._preview_active = False
            self._preview_type = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping preview: {e}")
            return False
    
    def configure(self, width: int = None, height: int = None, **kwargs) -> bool:
        """
        Configure preview settings
        
        Args:
            width: Preview width
            height: Preview height
            **kwargs: Additional configuration parameters
            
        Returns:
            bool: True if configured successfully
        """
        if not self._preview_active:
            logger.warning("Cannot configure inactive preview")
            return False
        
        try:
            logger.info("Configuring preview")
            
            # Update configuration
            config = self._preview_config.copy()
            
            if width is not None:
                config['width'] = width
            
            if height is not None:
                config['height'] = height
            
            # Add any additional parameters
            config.update(kwargs)
            
            # Restart preview with new configuration
            preview_type = self._preview_type
            self.stop()
            result = self.start(preview_type=preview_type, **config)
            
            return result
            
        except Exception as e:
            logger.error(f"Error configuring preview: {e}")
            return False
    
    @property
    def is_active(self) -> bool:
        """Check if preview is active"""
        return self._preview_active
    
    @property
    def preview_type(self) -> str:
        """Get current preview type"""
        return self._preview_type if self._preview_active else None
    
    @property
    def preview_config(self) -> Dict[str, Any]:
        """Get current preview configuration"""
        return self._preview_config.copy()
