"""
MJPEGEncoding - Motion JPEG video encoding service

This module provides functionality for recording Motion JPEG (MJPEG) video,
which encodes each frame as a JPEG image.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
import threading
import os

# Import base service
from .encoding_service import EncodingService

# Setup logging
logger = logging.getLogger(__name__)


class MJPEGEncoding(EncodingService):
    """
    Motion JPEG video encoding service
    
    This class provides functionality for recording Motion JPEG (MJPEG) video,
    which encodes each frame as a JPEG image.
    """
    
    def __init__(self, picam2):
        """
        Initialize MJPEG encoding service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        super().__init__(picam2)
        logger.debug("MJPEGEncoding service initialized")
    
    def start_recording(self, output_file: str, quality: int = 90, fps: int = 30,
                      duration: float = None, **kwargs) -> bool:
        """
        Start MJPEG video recording
        
        Args:
            output_file: Path to save video file
            quality: JPEG quality (0-100)
            fps: Frames per second
            duration: Recording duration in seconds (None for manual stop)
            **kwargs: Additional encoding parameters
            
        Returns:
            bool: True if recording started successfully
        """
        with self._lock:
            if self._recording:
                logger.warning("Recording already in progress")
                return False
            
            try:
                logger.info(f"Starting MJPEG recording to {output_file}")
                
                # Import MJPEG encoder
                from picamera2.encoders import MJPEGEncoder
                
                # Create encoder
                self._encoder = MJPEGEncoder(
                    q=quality,
                    fps=fps,
                    **{k: v for k, v in kwargs.items() if k not in ('quality', 'fps')}
                )
                
                # Start recording
                self._output = output_file
                self._picam2.start_recording(self._encoder, self._output)
                
                # Update recording state
                self._recording = True
                self._recording_file = output_file
                self._recording_start_time = time.time()
                self._recording_duration = duration
                
                # Schedule stop if duration specified
                if duration:
                    stop_thread = threading.Thread(
                        target=self._stop_after_duration,
                        args=(duration,),
                        daemon=True
                    )
                    stop_thread.start()
                
                logger.info(f"MJPEG recording started with quality {quality}, {fps} fps")
                return True
                
            except Exception as e:
                logger.error(f"MJPEG recording start error: {e}")
                return False
    
    def stop_recording(self) -> bool:
        """
        Stop MJPEG video recording
        
        Returns:
            bool: True if recording stopped successfully
        """
        with self._lock:
            if not self._recording:
                logger.warning("No recording in progress")
                return True
            
            try:
                logger.info("Stopping MJPEG recording")
                
                # Stop recording
                self._picam2.stop_recording()
                
                # Reset recording state
                self._recording = False
                self._encoder = None
                recording_file = self._recording_file
                self._recording_file = None
                
                # Calculate recording duration
                if self._recording_start_time > 0:
                    duration = time.time() - self._recording_start_time
                    logger.info(f"Recording completed: {recording_file} ({duration:.1f} seconds)")
                
                return True
                
            except Exception as e:
                logger.error(f"MJPEG recording stop error: {e}")
                return False
    
    def _stop_after_duration(self, duration: float):
        """Stop recording after specified duration"""
        try:
            time.sleep(duration)
            if self._recording:
                logger.info(f"Auto-stopping recording after {duration}s")
                self.stop_recording()
        except Exception as e:
            logger.error(f"Error in timed stop: {e}")
    
    def set_quality(self, quality: int) -> bool:
        """
        Set JPEG quality during recording
        
        Args:
            quality: New JPEG quality (0-100)
            
        Returns:
            bool: True if quality changed successfully
        """
        with self._lock:
            if not self._recording or not self._encoder:
                logger.warning("No active recording to update quality")
                return False
            
            try:
                logger.debug(f"Setting JPEG quality to {quality}")
                
                if hasattr(self._encoder, 'set_q'):
                    self._encoder.set_q(quality)
                    return True
                else:
                    logger.warning("Quality change not supported by encoder")
                    return False
                
            except Exception as e:
                logger.error(f"Error setting quality: {e}")
                return False
