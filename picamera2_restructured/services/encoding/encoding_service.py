"""
EncodingService - Base service for video encoding functionality

This module provides the base service class for video encoding functionality,
which is extended by specific encoder implementations.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
import threading
import os

# Setup logging
logger = logging.getLogger(__name__)


class EncodingService:
    """
    Base service for video encoding
    
    This class provides common functionality for all encoding services
    and is extended by specific implementations.
    """
    
    def __init__(self, picam2):
        """
        Initialize encoding service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        self._picam2 = picam2
        self._lock = threading.RLock()
        self._recording = False
        self._encoder = None
        self._output = None
        self._recording_file = None
        self._recording_start_time = 0
        self._recording_duration = 0
        
        # Default encoding parameters
        self._default_params = {
            'bitrate': 10000000,  # 10 Mbps
            'fps': 30,
            'quality': 'medium',
            'intra_period': 30,  # I-frame interval
        }
        
        logger.debug("EncodingService initialized")
    
    def start_recording(self, output_file: str, **kwargs) -> bool:
        """
        Start video recording
        
        Args:
            output_file: Path to save video file
            **kwargs: Encoding parameters
            
        Returns:
            bool: True if recording started successfully
        """
        with self._lock:
            if self._recording:
                logger.warning("Recording already in progress")
                return False
            
            try:
                logger.debug(f"Starting recording to {output_file}")
                
                # Override in subclasses
                return False
                
            except Exception as e:
                logger.error(f"Recording start error: {e}")
                return False
    
    def stop_recording(self) -> bool:
        """
        Stop video recording
        
        Returns:
            bool: True if recording stopped successfully
        """
        with self._lock:
            if not self._recording:
                logger.warning("No recording in progress")
                return False
            
            try:
                logger.debug("Stopping recording")
                
                # Override in subclasses
                return False
                
            except Exception as e:
                logger.error(f"Recording stop error: {e}")
                return False
    
    def pause_recording(self) -> bool:
        """
        Pause video recording
        
        Returns:
            bool: True if recording paused successfully
        """
        with self._lock:
            if not self._recording:
                logger.warning("No recording in progress")
                return False
            
            try:
                logger.debug("Pausing recording")
                
                if hasattr(self._picam2, 'stop_encoder'):
                    self._picam2.stop_encoder()
                    return True
                else:
                    logger.warning("Pause not supported by encoder")
                    return False
                
            except Exception as e:
                logger.error(f"Recording pause error: {e}")
                return False
    
    def resume_recording(self) -> bool:
        """
        Resume video recording
        
        Returns:
            bool: True if recording resumed successfully
        """
        with self._lock:
            if not self._recording:
                logger.warning("No recording in progress")
                return False
            
            try:
                logger.debug("Resuming recording")
                
                if hasattr(self._picam2, 'start_encoder'):
                    self._picam2.start_encoder()
                    return True
                else:
                    logger.warning("Resume not supported by encoder")
                    return False
                
            except Exception as e:
                logger.error(f"Recording resume error: {e}")
                return False
    
    def capture_while_recording(self, output_file: str) -> bool:
        """
        Capture still image during recording
        
        Args:
            output_file: Path to save the image
            
        Returns:
            bool: True if capture successful
        """
        if not self._recording:
            logger.warning("No recording in progress")
            return False
        
        try:
            logger.debug(f"Capturing still during recording: {output_file}")
            
            self._picam2.capture_file(output_file)
            return True
            
        except Exception as e:
            logger.error(f"Still capture error: {e}")
            return False
    
    def get_recording_stats(self) -> Dict[str, Any]:
        """
        Get recording statistics
        
        Returns:
            Dict with recording statistics
        """
        stats = {
            'recording': self._recording,
            'file': self._recording_file,
        }
        
        if self._recording and self._recording_start_time > 0:
            elapsed = time.time() - self._recording_start_time
            stats['elapsed'] = elapsed
            
            if self._recording_duration > 0:
                stats['duration'] = self._recording_duration
                stats['progress'] = min(100, (elapsed / self._recording_duration) * 100)
        
        return stats
    
    @property
    def is_recording(self) -> bool:
        """Check if recording is in progress"""
        return self._recording
    
    @property
    def recording_file(self) -> Optional[str]:
        """Get current recording file path"""
        return self._recording_file if self._recording else None
