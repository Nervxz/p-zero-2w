"""
EncodingAPI - Simplified interface for video recording and encoding

This module provides easy-to-use methods for video recording, encoding settings,
and other multimedia operations.

Usage:
    from picamera2_restructured import CameraController
    
    camera = CameraController()
    camera.initialize()
    
    # Record video
    camera.encoding.start_video_recording("video.mp4")
    time.sleep(5)
    camera.encoding.stop_video_recording()
    
    # Record with custom settings
    camera.encoding.start_video_recording(
        "hq_video.mp4", 
        quality="high", 
        fps=60,
        encoder_type="libav"
    )
"""

import time
import logging
import os
from typing import Dict, Any, Optional, List, Union
import threading

# Setup logging
logger = logging.getLogger(__name__)


class EncodingAPI:
    """
    High-level encoding API for PiCamera2
    Provides simplified methods for video recording and encoding
    """
    
    def __init__(self, picam2):
        """
        Initialize encoding API
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        self._picam2 = picam2
        self._recording = False
        self._encoder = None
        self._output = None
        self._recording_file = None
        self._recording_thread = None
        
        # Default encoding configuration
        self._encoding_config = {
            'quality': 'medium',
            'bitrate': 10000000,  # 10 Mbps
            'fps': 30,
            'encoder_type': 'h264',
        }
    
    def start_video_recording(self, output_file: str, 
                             quality: str = None,
                             fps: int = None, 
                             bitrate: int = None, 
                             encoder_type: str = None,
                             duration: float = None,
                             **kwargs) -> bool:
        """
        Start video recording
        
        Args:
            output_file: Path to save video file
            quality: Recording quality ('low', 'medium', 'high')
            fps: Frames per second
            bitrate: Encoding bitrate
            encoder_type: Encoder type ('h264', 'mjpeg', 'libav')
            duration: Recording duration in seconds (None for manual stop)
            **kwargs: Additional encoder parameters
            
        Returns:
            bool: True if recording started successfully
        """
        if self._recording:
            logger.warning("Recording already in progress")
            return False
        
        try:
            logger.info(f"Starting video recording to {output_file}")
            
            # Prepare configuration
            config = self._encoding_config.copy()
            
            # Override with provided values
            if quality:
                config['quality'] = quality
                
                # Set bitrate based on quality if not explicitly provided
                if not bitrate:
                    if quality == 'low':
                        config['bitrate'] = 5000000  # 5 Mbps
                    elif quality == 'high':
                        config['bitrate'] = 20000000  # 20 Mbps
            
            if fps:
                config['fps'] = fps
            
            if bitrate:
                config['bitrate'] = bitrate
            
            if encoder_type:
                config['encoder_type'] = encoder_type
            
            # Add any additional parameters
            config.update(kwargs)
            
            # Select encoder based on type
            if config['encoder_type'].lower() == 'libav':
                self._start_libav_recording(output_file, config)
            elif config['encoder_type'].lower() == 'mjpeg':
                self._start_mjpeg_recording(output_file, config)
            else:
                # Default to H.264
                self._start_h264_recording(output_file, config)
            
            # Set recording state
            self._recording = True
            self._recording_file = output_file
            
            # Start timed recording if duration specified
            if duration:
                self._recording_thread = threading.Thread(
                    target=self._stop_after_duration,
                    args=(duration,)
                )
                self._recording_thread.daemon = True
                self._recording_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting video recording: {e}")
            return False
    
    def _start_h264_recording(self, output_file: str, config: Dict[str, Any]):
        """Start H.264 video recording with specified config"""
        from picamera2.encoders import H264Encoder
        
        # Create encoder
        self._encoder = H264Encoder(
            bitrate=config['bitrate'],
            repeat=True,
            **{k: v for k, v in config.items() if k not in ['quality', 'bitrate', 'fps', 'encoder_type']}
        )
        
        # Start encoder
        self._output = output_file
        self._picam2.start_recording(self._encoder, self._output)
    
    def _start_mjpeg_recording(self, output_file: str, config: Dict[str, Any]):
        """Start MJPEG video recording with specified config"""
        from picamera2.encoders import MJPEGEncoder
        
        # Create encoder
        q = 95
        if config['quality'] == 'low':
            q = 75
        elif config['quality'] == 'high':
            q = 100
        
        self._encoder = MJPEGEncoder(
            q=q,
            fps=config['fps'],
            **{k: v for k, v in config.items() if k not in ['quality', 'bitrate', 'fps', 'encoder_type']}
        )
        
        # Start encoder
        self._output = output_file
        self._picam2.start_recording(self._encoder, self._output)
    
    def _start_libav_recording(self, output_file: str, config: Dict[str, Any]):
        """Start LibAV video recording with specified config"""
        try:
            import pyav
            from picamera2.encoders import LibavH264Encoder
            
            # Create encoder
            self._encoder = LibavH264Encoder(
                bitrate=config['bitrate'],
                fps=config['fps'],
                **{k: v for k, v in config.items() if k not in ['quality', 'bitrate', 'fps', 'encoder_type']}
            )
            
            # Start encoder
            self._output = output_file
            self._picam2.start_recording(self._encoder, self._output)
            
        except ImportError:
            logger.error("LibAV encoder requires PyAV package. Falling back to H264Encoder")
            self._start_h264_recording(output_file, config)
    
    def _stop_after_duration(self, duration: float):
        """Helper method to stop recording after specified duration"""
        time.sleep(duration)
        if self._recording:
            self.stop_video_recording()
    
    def stop_video_recording(self) -> bool:
        """
        Stop video recording
        
        Returns:
            bool: True if recording stopped successfully
        """
        if not self._recording:
            logger.warning("No active recording to stop")
            return False
        
        try:
            logger.info("Stopping video recording")
            
            self._picam2.stop_recording()
            
            # Reset recording state
            self._recording = False
            self._encoder = None
            self._output = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping video recording: {e}")
            return False
    
    def pause_recording(self) -> bool:
        """
        Pause video recording
        
        Returns:
            bool: True if recording paused successfully
        """
        if not self._recording:
            return False
        
        try:
            logger.info("Pausing recording")
            self._picam2.stop_encoder()
            return True
        except Exception as e:
            logger.error(f"Error pausing recording: {e}")
            return False
    
    def resume_recording(self) -> bool:
        """
        Resume paused recording
        
        Returns:
            bool: True if recording resumed successfully
        """
        if not self._recording:
            return False
        
        try:
            logger.info("Resuming recording")
            self._picam2.start_encoder()
            return True
        except Exception as e:
            logger.error(f"Error resuming recording: {e}")
            return False
    
    def capture_while_recording(self, output_file: str) -> bool:
        """
        Capture still image during video recording
        
        Args:
            output_file: Path to save image file
            
        Returns:
            bool: True if capture succeeded
        """
        if not self._recording:
            logger.warning("No active recording")
            return False
        
        try:
            logger.info(f"Capturing still during recording to {output_file}")
            
            # Determine format from filename
            format_name = os.path.splitext(output_file)[1].lower().replace('.', '')
            
            if format_name in ('jpg', 'jpeg'):
                array = self._picam2.capture_array()
                
                from PIL import Image
                import numpy as np
                
                # Convert and save
                if isinstance(array, np.ndarray):
                    img = Image.fromarray(array)
                    img.save(output_file)
                    return True
            
            # Default capture method
            self._picam2.capture_file(output_file)
            return True
            
        except Exception as e:
            logger.error(f"Error capturing while recording: {e}")
            return False
    
    def configure_encoding(self, config: Dict[str, Any]) -> bool:
        """
        Configure encoding settings
        
        Args:
            config: Encoding configuration
            
        Returns:
            bool: True if configured successfully
        """
        try:
            logger.info("Updating encoding configuration")
            self._encoding_config.update(config)
            return True
        except Exception as e:
            logger.error(f"Error configuring encoding: {e}")
            return False
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self._recording
    
    @property
    def recording_file(self) -> Optional[str]:
        """Get current recording file path"""
        return self._recording_file if self._recording else None
    
    @property
    def encoding_config(self) -> Dict[str, Any]:
        """Get current encoding configuration"""
        return self._encoding_config.copy()
    
    def set_quality(self, quality: str) -> bool:
        """
        Set recording quality
        
        Args:
            quality: Quality level ('low', 'medium', 'high')
            
        Returns:
            bool: True if quality set successfully
        """
        if quality not in ('low', 'medium', 'high'):
            logger.warning(f"Invalid quality: {quality}")
            return False
        
        try:
            self._encoding_config['quality'] = quality
            
            # Update bitrate based on quality
            if quality == 'low':
                self._encoding_config['bitrate'] = 5000000  # 5 Mbps
            elif quality == 'medium':
                self._encoding_config['bitrate'] = 10000000  # 10 Mbps
            else:  # high
                self._encoding_config['bitrate'] = 20000000  # 20 Mbps
                
            return True
            
        except Exception as e:
            logger.error(f"Error setting quality: {e}")
            return False
