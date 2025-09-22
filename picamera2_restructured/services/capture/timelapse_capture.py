"""
TimelapseCapture - Timelapse image capture service

This module provides functionality for capturing timelapse image sequences
over extended periods.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
import threading
import os
import datetime

# Import base service
from .capture_service import CaptureService
from .image_capture import ImageCapture

# Setup logging
logger = logging.getLogger(__name__)


class TimelapseCapture(CaptureService):
    """
    Timelapse image capture service
    
    This class provides functionality for capturing timelapse image sequences
    over extended periods.
    """
    
    def __init__(self, picam2):
        """
        Initialize timelapse capture service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        super().__init__(picam2)
        self._image_capture = ImageCapture(picam2)
        
        # Timelapse state
        self._is_running = False
        self._stop_requested = False
        self._timelapse_thread = None
        self._timelapse_interval = 0
        self._timelapse_duration = 0
        self._timelapse_start_time = 0
        self._timelapse_count = 0
        
        logger.debug("TimelapseCapture service initialized")
    
    def start_timelapse(self, interval: float, duration: float = None, count: int = None,
                      output_dir: str = None, format: str = 'jpeg', quality: int = 95,
                      callback: Callable = None, **kwargs) -> bool:
        """
        Start timelapse capture
        
        Args:
            interval: Time interval between captures (seconds)
            duration: Total duration of timelapse (seconds, None for unlimited)
            count: Number of images to capture (None for unlimited or based on duration)
            output_dir: Directory to save images (None for no saving)
            format: Image format
            quality: Image quality for JPEG
            callback: Function to call for each image (receives image, index, timestamp)
            **kwargs: Additional capture parameters
            
        Returns:
            bool: True if timelapse started successfully
        """
        with self._lock:
            if self._is_running:
                logger.warning("Timelapse already running")
                return False
            
            try:
                logger.info(f"Starting timelapse with interval {interval}s")
                
                # Calculate count if duration provided but count not
                if duration is not None and count is None:
                    count = int(duration / interval) + 1
                
                # Create output directory if needed
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                
                # Reset state
                self._stop_requested = False
                self._timelapse_interval = interval
                self._timelapse_duration = duration
                self._timelapse_start_time = time.time()
                self._timelapse_count = 0
                
                # Start timelapse thread
                self._timelapse_thread = threading.Thread(
                    target=self._timelapse_loop,
                    args=(interval, duration, count, output_dir, format, quality, callback, kwargs),
                    daemon=True
                )
                self._timelapse_thread.start()
                
                self._is_running = True
                return True
                
            except Exception as e:
                logger.error(f"Failed to start timelapse: {e}")
                self._is_running = False
                return False
    
    def _timelapse_loop(self, interval: float, duration: float, count: int, 
                      output_dir: str, format: str, quality: int,
                      callback: Callable, kwargs: Dict[str, Any]):
        """Timelapse capture loop running in a separate thread"""
        try:
            logger.debug("Timelapse thread started")
            
            start_time = time.time()
            image_count = 0
            
            while True:
                # Check if stop requested
                if self._stop_requested:
                    logger.debug("Timelapse stop requested")
                    break
                
                # Check if count reached
                if count is not None and image_count >= count:
                    logger.debug(f"Timelapse count reached: {count}")
                    break
                
                # Check if duration exceeded
                current_time = time.time()
                elapsed = current_time - start_time
                
                if duration is not None and elapsed >= duration:
                    logger.debug(f"Timelapse duration reached: {duration}s")
                    break
                
                # Capture image
                try:
                    image = self._image_capture.capture(format=format, quality=quality, **kwargs)
                    
                    if image is not None:
                        # Update count
                        image_count += 1
                        self._timelapse_count = image_count
                        
                        # Generate timestamp
                        timestamp = datetime.datetime.now()
                        
                        # Save if output_dir provided
                        if output_dir:
                            # Generate filename
                            filename = f"timelapse_{timestamp.strftime('%Y%m%d_%H%M%S')}.{format.lower()}"
                            if format.lower() == 'jpg':
                                filename = f"timelapse_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                            
                            file_path = os.path.join(output_dir, filename)
                            
                            try:
                                if isinstance(image, bytes):
                                    with open(file_path, 'wb') as f:
                                        f.write(image)
                                else:
                                    # Handle numpy array
                                    from PIL import Image as PILImage
                                    img = PILImage.fromarray(image)
                                    img.save(file_path)
                            except Exception as e:
                                logger.error(f"Error saving timelapse image: {e}")
                        
                        # Call callback if provided
                        if callback:
                            try:
                                callback(image, image_count, timestamp)
                            except Exception as e:
                                logger.error(f"Error in timelapse callback: {e}")
                    
                except Exception as e:
                    logger.error(f"Error capturing timelapse image: {e}")
                
                # Sleep until next interval
                # Calculate sleep time to maintain accurate intervals
                current_time = time.time()
                elapsed_since_start = current_time - start_time
                next_capture_time = start_time + (image_count * interval)
                sleep_time = next_capture_time - current_time
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            logger.info(f"Timelapse completed with {image_count} images")
            
        except Exception as e:
            logger.error(f"Error in timelapse loop: {e}")
        finally:
            self._is_running = False
    
    def stop_timelapse(self) -> bool:
        """
        Stop timelapse capture
        
        Returns:
            bool: True if stop request sent successfully
        """
        with self._lock:
            if not self._is_running:
                logger.warning("No timelapse running to stop")
                return False
            
            try:
                logger.info("Stopping timelapse")
                self._stop_requested = True
                
                # Wait for thread to finish with timeout
                if self._timelapse_thread:
                    self._timelapse_thread.join(timeout=2.0)
                
                self._is_running = False
                return True
                
            except Exception as e:
                logger.error(f"Error stopping timelapse: {e}")
                return False
    
    @property
    def is_running(self) -> bool:
        """Check if timelapse is currently running"""
        return self._is_running
    
    @property
    def timelapse_stats(self) -> Dict[str, Any]:
        """
        Get timelapse statistics
        
        Returns:
            Dict with timelapse statistics
        """
        stats = {
            'running': self._is_running,
            'count': self._timelapse_count,
            'interval': self._timelapse_interval,
        }
        
        if self._is_running and self._timelapse_start_time > 0:
            elapsed = time.time() - self._timelapse_start_time
            stats['elapsed'] = elapsed
            stats['duration'] = self._timelapse_duration
            
            if self._timelapse_duration:
                stats['progress'] = min(100, (elapsed / self._timelapse_duration) * 100)
        
        return stats
