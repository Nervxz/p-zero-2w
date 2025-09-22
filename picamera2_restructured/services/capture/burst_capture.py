"""
BurstCapture - Burst image capture service

This module provides functionality for capturing multiple images
in quick succession (burst mode).
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
import threading
import os
import numpy as np
import io

# Import base service
from .capture_service import CaptureService
from .image_capture import ImageCapture

# Setup logging
logger = logging.getLogger(__name__)


class BurstCapture(CaptureService):
    """
    Burst image capture service
    
    This class provides functionality for capturing multiple images
    in quick succession (burst mode).
    """
    
    def __init__(self, picam2):
        """
        Initialize burst capture service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        super().__init__(picam2)
        self._image_capture = ImageCapture(picam2)
        logger.debug("BurstCapture service initialized")
    
    def capture(self, count: int = 5, interval: float = 0.0, format: str = 'jpeg', 
              quality: int = 95, **kwargs) -> List[Union[bytes, np.ndarray]]:
        """
        Capture a burst of images
        
        Args:
            count: Number of images to capture
            interval: Time interval between captures (seconds)
            format: Image format
            quality: Image quality for JPEG
            **kwargs: Additional capture parameters
            
        Returns:
            List of captured images
        """
        with self._lock:
            try:
                # Call parent method for tracking
                super().capture()
                
                logger.debug(f"Capturing burst of {count} images")
                
                images = []
                
                for i in range(count):
                    # Capture single image
                    img = self._image_capture.capture(format=format, quality=quality, **kwargs)
                    
                    if img is not None:
                        images.append(img)
                    
                    # Wait for interval if not last image
                    if i < count - 1 and interval > 0:
                        time.sleep(interval)
                
                logger.debug(f"Burst capture completed, captured {len(images)} of {count} images")
                return images
                
            except Exception as e:
                logger.error(f"Burst capture error: {e}")
                return []
    
    def capture_files(self, base_path: str, count: int = 5, interval: float = 0.0, 
                    format: str = 'jpeg', quality: int = 95, **kwargs) -> List[str]:
        """
        Capture burst directly to files
        
        Args:
            base_path: Base path for saved files
            count: Number of images to capture
            interval: Time interval between captures (seconds)
            format: Image format
            quality: Image quality for JPEG
            **kwargs: Additional capture parameters
            
        Returns:
            List of saved file paths
        """
        try:
            logger.debug(f"Capturing burst to files: {base_path}")
            
            # Determine file extension
            if format.lower() in ('jpeg', 'jpg'):
                ext = '.jpg'
            elif format.lower() == 'png':
                ext = '.png'
            elif format.lower() == 'raw':
                ext = '.raw'
            else:
                ext = f'.{format}'
            
            # Generate file paths
            file_paths = []
            base_name, base_ext = os.path.splitext(base_path)
            
            if base_ext:
                # Use provided extension
                ext = base_ext
            
            for i in range(count):
                file_paths.append(f"{base_name}_{i:03d}{ext}")
            
            # Capture images
            images = self.capture(count=count, interval=interval, format=format, 
                                quality=quality, **kwargs)
            
            # Save images to files
            saved_paths = []
            
            for i, image in enumerate(images):
                if i < len(file_paths):
                    try:
                        file_path = file_paths[i]
                        
                        if isinstance(image, bytes):
                            with open(file_path, 'wb') as f:
                                f.write(image)
                        else:
                            # Handle numpy array
                            from PIL import Image
                            img = Image.fromarray(image)
                            img.save(file_path)
                        
                        saved_paths.append(file_path)
                    except Exception as e:
                        logger.error(f"Error saving burst image {i}: {e}")
            
            logger.debug(f"Burst capture saved {len(saved_paths)} of {count} images")
            return saved_paths
            
        except Exception as e:
            logger.error(f"Burst file capture error: {e}")
            return []
    
    def capture_continuous(self, callback: Callable, count: int = 10, 
                         interval: float = 1.0, format: str = 'array', **kwargs) -> bool:
        """
        Continuously capture images with callback
        
        Args:
            callback: Function to call for each image (receives image, index)
            count: Number of images to capture
            interval: Time interval between captures (seconds)
            format: Image format
            **kwargs: Additional capture parameters
            
        Returns:
            bool: True if completed successfully
        """
        try:
            logger.debug(f"Starting continuous capture for {count} images")
            
            for i in range(count):
                # Capture single image
                img = self._image_capture.capture(format=format, **kwargs)
                
                if img is not None:
                    # Call the callback with the image
                    try:
                        callback(img, i)
                    except Exception as e:
                        logger.error(f"Error in callback for image {i}: {e}")
                
                # Wait for interval if not last image
                if i < count - 1:
                    time.sleep(interval)
            
            logger.debug("Continuous capture completed")
            return True
            
        except Exception as e:
            logger.error(f"Continuous capture error: {e}")
            return False
    
    def capture_bracketed(self, exposures: List[int], format: str = 'jpeg', **kwargs) -> List[Union[bytes, np.ndarray]]:
        """
        Capture bracketed exposures
        
        Args:
            exposures: List of exposure times in microseconds
            format: Image format
            **kwargs: Additional capture parameters
            
        Returns:
            List of captured images
        """
        with self._lock:
            try:
                logger.debug(f"Capturing bracketed exposures: {exposures}")
                
                images = []
                original_exposure = None
                
                try:
                    # Get current exposure setting
                    if self._picam2.camera_controls:
                        original_exposure = self._picam2.camera_controls.get('ExposureTime')
                except:
                    pass
                
                # Capture with each exposure
                for exp in exposures:
                    try:
                        # Set exposure
                        self._picam2.set_controls({"ExposureTime": exp})
                        
                        # Allow exposure to take effect
                        time.sleep(0.1)
                        
                        # Capture image
                        img = self._image_capture.capture(format=format, **kwargs)
                        
                        if img is not None:
                            images.append(img)
                            
                    except Exception as e:
                        logger.error(f"Error capturing with exposure {exp}: {e}")
                
                # Restore original exposure
                if original_exposure is not None:
                    try:
                        self._picam2.set_controls({"ExposureTime": original_exposure})
                    except:
                        pass
                
                logger.debug(f"Bracketed capture completed, captured {len(images)} of {len(exposures)} images")
                return images
                
            except Exception as e:
                logger.error(f"Bracketed capture error: {e}")
                return []
