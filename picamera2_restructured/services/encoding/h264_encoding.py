"""
H264Encoding - H.264 video encoding service

This module provides functionality for recording H.264 encoded video.
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


class H264Encoding(EncodingService):
    """
    H.264 video encoding service
    
    This class provides functionality for recording H.264 encoded video,
    which is widely supported and offers good compression.
    """
    
    def __init__(self, picam2):
        """
        Initialize H.264 encoding service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        super().__init__(picam2)
        
        # H.264-specific default parameters
        self._default_params.update({
            'profile': 'high',
            'level': '4.2',
        })
        
        logger.debug("H264Encoding service initialized")
    
    def start_recording(self, output_file: str, bitrate: int = None, 
                      quality: str = None, fps: int = None, 
                      duration: float = None, **kwargs) -> bool:
        """
        Start H.264 video recording
        
        Args:
            output_file: Path to save video file
            bitrate: Encoding bitrate (bits/sec)
            quality: Quality preset ('low', 'medium', 'high')
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
                logger.info(f"Starting H.264 recording to {output_file}")
                
                # Determine bitrate from quality if not explicitly set
                if bitrate is None:
                    if quality == 'low':
                        bitrate = 5000000  # 5 Mbps
                    elif quality == 'high':
                        bitrate = 20000000  # 20 Mbps
                    else:
                        # Default medium quality
                        bitrate = 10000000  # 10 Mbps
                
                # Import H.264 encoder
                from picamera2.encoders import H264Encoder
                
                # Create encoder
                encoder_args = {
                    'bitrate': bitrate,
                }
                
                # Add additional parameters
                for param, default in self._default_params.items():
                    if param not in ('bitrate', 'quality'):
                        encoder_args[param] = kwargs.get(param, default)
                
                self._encoder = H264Encoder(**encoder_args)
                
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
                
                logger.info(f"H.264 recording started with bitrate {bitrate/1000000:.1f} Mbps")
                return True
                
            except Exception as e:
                logger.error(f"H.264 recording start error: {e}")
                return False
    
    def stop_recording(self) -> bool:
        """
        Stop H.264 video recording
        
        Returns:
            bool: True if recording stopped successfully
        """
        with self._lock:
            if not self._recording:
                logger.warning("No recording in progress")
                return True
            
            try:
                logger.info("Stopping H.264 recording")
                
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
                logger.error(f"H.264 recording stop error: {e}")
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
    
    def set_bitrate(self, bitrate: int) -> bool:
        """
        Set encoding bitrate during recording
        
        Args:
            bitrate: New bitrate in bits/sec
            
        Returns:
            bool: True if bitrate changed successfully
        """
        with self._lock:
            if not self._recording or not self._encoder:
                logger.warning("No active recording to update bitrate")
                return False
            
            try:
                logger.debug(f"Setting bitrate to {bitrate/1000000:.1f} Mbps")
                
                if hasattr(self._encoder, 'set_bitrate'):
                    self._encoder.set_bitrate(bitrate)
                    return True
                else:
                    logger.warning("Bitrate change not supported by encoder")
                    return False
                
            except Exception as e:
                logger.error(f"Error setting bitrate: {e}")
                return False
    
    def set_quantization_parameter(self, qp: int) -> bool:
        """
        Set quantization parameter (constant QP mode)
        
        Args:
            qp: Quantization parameter (0-51, lower is higher quality)
            
        Returns:
            bool: True if QP set successfully
        """
        with self._lock:
            if not self._recording or not self._encoder:
                logger.warning("No active recording to set QP")
                return False
            
            try:
                logger.debug(f"Setting QP to {qp}")
                
                if hasattr(self._encoder, 'set_qp'):
                    self._encoder.set_qp(qp)
                    return True
                else:
                    logger.warning("QP setting not supported by encoder")
                    return False
                
            except Exception as e:
                logger.error(f"Error setting QP: {e}")
                return False
