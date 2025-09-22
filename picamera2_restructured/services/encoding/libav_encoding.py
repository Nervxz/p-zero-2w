"""
LibavEncoding - FFmpeg/LibAV-based video encoding service

This module provides functionality for recording video using FFmpeg/LibAV,
which enables advanced codec options and formats.
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


class LibavEncoding(EncodingService):
    """
    FFmpeg/LibAV-based video encoding service
    
    This class provides functionality for recording video using FFmpeg/LibAV,
    which enables advanced codec options and formats.
    """
    
    def __init__(self, picam2):
        """
        Initialize LibAV encoding service
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        super().__init__(picam2)
        
        # Check for PyAV
        self._pyav_available = self._check_pyav_availability()
        
        logger.debug(f"LibavEncoding service initialized (PyAV {'available' if self._pyav_available else 'not available'})")
    
    def _check_pyav_availability(self) -> bool:
        """Check if PyAV is available"""
        try:
            import av
            return True
        except ImportError:
            logger.warning("PyAV not found. LibAV encoding will not be available.")
            return False
    
    def start_recording(self, output_file: str, codec: str = 'h264', bitrate: int = None,
                      quality: str = None, fps: int = None, audio: bool = False,
                      duration: float = None, **kwargs) -> bool:
        """
        Start recording with LibAV encoder
        
        Args:
            output_file: Path to save video file
            codec: Video codec ('h264', 'hevc', 'mjpeg', etc.)
            bitrate: Encoding bitrate (bits/sec)
            quality: Quality preset ('low', 'medium', 'high')
            fps: Frames per second
            audio: Include audio recording
            duration: Recording duration in seconds (None for manual stop)
            **kwargs: Additional encoding parameters
            
        Returns:
            bool: True if recording started successfully
        """
        with self._lock:
            if self._recording:
                logger.warning("Recording already in progress")
                return False
            
            if not self._pyav_available:
                logger.error("Cannot start LibAV recording - PyAV not available")
                return False
            
            try:
                logger.info(f"Starting LibAV recording to {output_file}")
                
                # Determine bitrate from quality if not explicitly set
                if bitrate is None:
                    if quality == 'low':
                        bitrate = 5000000  # 5 Mbps
                    elif quality == 'high':
                        bitrate = 20000000  # 20 Mbps
                    else:
                        # Default medium quality
                        bitrate = 10000000  # 10 Mbps
                
                # Set fps default
                if fps is None:
                    fps = 30
                
                # Import encoder based on codec
                if codec.lower() == 'h264':
                    from picamera2.encoders import LibavH264Encoder as Encoder
                else:
                    logger.error(f"Unsupported codec for LibAV encoding: {codec}")
                    return False
                
                # Create encoder
                encoder_args = {
                    'bitrate': bitrate,
                    'fps': fps,
                }
                
                # Add audio options
                if audio:
                    encoder_args['audio'] = True
                
                # Add additional parameters
                for key, value in kwargs.items():
                    if key not in ('bitrate', 'fps', 'quality', 'audio'):
                        encoder_args[key] = value
                
                self._encoder = Encoder(**encoder_args)
                
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
                
                logger.info(f"LibAV recording started with codec {codec}, {fps} fps, {bitrate/1000000:.1f} Mbps")
                return True
                
            except Exception as e:
                logger.error(f"LibAV recording start error: {e}")
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
                return True
            
            try:
                logger.info("Stopping LibAV recording")
                
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
                logger.error(f"LibAV recording stop error: {e}")
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
    
    def is_available(self) -> bool:
        """
        Check if LibAV encoding is available
        
        Returns:
            bool: True if PyAV is available
        """
        return self._pyav_available
    
    def get_supported_codecs(self) -> List[str]:
        """
        Get list of supported codecs
        
        Returns:
            List of codec names
        """
        if not self._pyav_available:
            return []
        
        try:
            import av
            return ['h264']  # Currently only h264 is implemented in picamera2
        except:
            return []
