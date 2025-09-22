"""
FormatUtils - Camera format and configuration utilities

This module provides utility functions for working with camera formats,
configurations, and other technical aspects of the camera system.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np

# Setup logging
logger = logging.getLogger(__name__)


class FormatUtils:
    """
    Utility functions for camera formats and configurations
    """
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """
        Get list of supported image formats
        
        Returns:
            List of supported format names
        """
        return ['JPEG', 'PNG', 'YUV420', 'RGB888', 'RAW', 'MJPEG', 'H264']
    
    @staticmethod
    def is_format_supported(format_name: str) -> bool:
        """
        Check if format is supported
        
        Args:
            format_name: Format name to check
            
        Returns:
            bool: True if format is supported
        """
        return format_name.upper() in FormatUtils.get_supported_formats()
    
    @staticmethod
    def get_pixel_format(format_name: str) -> str:
        """
        Get libcamera pixel format for named format
        
        Args:
            format_name: Format name
            
        Returns:
            Corresponding libcamera pixel format
        """
        formats = {
            'JPEG': 'MJPEG',
            'YUV420': 'YUV420',
            'RGB888': 'RGB888',
            'RAW': 'RAW',
            'MJPEG': 'MJPEG',
            'H264': 'H264',
        }
        
        return formats.get(format_name.upper(), 'MJPEG')
    
    @staticmethod
    def guess_file_format(filename: str) -> str:
        """
        Guess format from filename extension
        
        Args:
            filename: Filename to check
            
        Returns:
            Format name
        """
        ext = filename.lower().split('.')[-1]
        
        formats = {
            'jpg': 'JPEG',
            'jpeg': 'JPEG',
            'png': 'PNG',
            'raw': 'RAW',
            'dng': 'DNG',
            'mp4': 'H264',
            'h264': 'H264',
            'mjpg': 'MJPEG',
            'mjpeg': 'MJPEG',
        }
        
        return formats.get(ext, 'JPEG')
    
    @staticmethod
    def get_optimal_buffer_size(width: int, height: int, format_name: str) -> int:
        """
        Calculate optimal buffer size for given format and dimensions
        
        Args:
            width: Image width
            height: Image height
            format_name: Format name
            
        Returns:
            Buffer size in bytes
        """
        format_name = format_name.upper()
        
        if format_name == 'RGB888' or format_name == 'BGR888':
            return width * height * 3
        elif format_name == 'YUV420':
            return int(width * height * 1.5)  # Y + U/2 + V/2
        elif format_name == 'MJPEG' or format_name == 'JPEG':
            return width * height  # Approximate - JPEG is compressed
        elif format_name == 'RAW' or format_name == 'DNG':
            return width * height * 2  # Typically 10-14 bit per pixel, rounded to 2 bytes
        elif format_name == 'H264':
            return width * height // 2  # Very approximate - H264 is compressed
        else:
            return width * height * 4  # Safe default
    
    @staticmethod
    def format_config_for_display(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format configuration dictionary for user-friendly display
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Formatted configuration dictionary
        """
        formatted = {}
        
        # Format main configuration sections
        for section in ['main', 'lores', 'raw']:
            if section in config:
                formatted[section] = {
                    'size': f"{config[section]['size'][0]}x{config[section]['size'][1]}",
                    'format': config[section].get('format', 'Unknown'),
                }
        
        # Format controls
        if 'controls' in config:
            formatted['controls'] = {}
            for key, value in config['controls'].items():
                # Format float values
                if isinstance(value, float):
                    formatted['controls'][key] = f"{value:.3f}"
                else:
                    formatted['controls'][key] = value
        
        # Add other sections
        for key, value in config.items():
            if key not in ['main', 'lores', 'raw', 'controls']:
                formatted[key] = value
        
        return formatted
    
    @staticmethod
    def get_stream_config_string(config: Dict[str, Any], stream: str = 'main') -> str:
        """
        Get human-readable string for stream configuration
        
        Args:
            config: Configuration dictionary
            stream: Stream name ('main', 'lores', 'raw')
            
        Returns:
            Human-readable configuration string
        """
        if stream not in config:
            return "Not configured"
        
        stream_config = config[stream]
        
        # Get size and format
        size = stream_config.get('size', (0, 0))
        format_name = stream_config.get('format', 'Unknown')
        
        return f"{size[0]}x{size[1]} {format_name}"
    
    @staticmethod
    def calculate_aspect_ratio(width: int, height: int) -> str:
        """
        Calculate aspect ratio as string
        
        Args:
            width: Width
            height: Height
            
        Returns:
            String representation of aspect ratio (e.g., "16:9")
        """
        def gcd(a, b):
            """Calculate greatest common divisor"""
            while b:
                a, b = b, a % b
            return a
        
        if width <= 0 or height <= 0:
            return "N/A"
        
        divisor = gcd(width, height)
        ratio_w = width // divisor
        ratio_h = height // divisor
        
        # Check for common aspect ratios
        if abs(ratio_w / ratio_h - 16 / 9) < 0.01:
            return "16:9"
        elif abs(ratio_w / ratio_h - 4 / 3) < 0.01:
            return "4:3"
        elif abs(ratio_w / ratio_h - 3 / 2) < 0.01:
            return "3:2"
        else:
            return f"{ratio_w}:{ratio_h}"
    
    @staticmethod
    def bytes_to_human_readable(bytes_value: int) -> str:
        """
        Convert bytes to human-readable string
        
        Args:
            bytes_value: Size in bytes
            
        Returns:
            Human-readable size string
        """
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        index = 0
        
        while bytes_value >= 1024 and index < len(suffixes) - 1:
            bytes_value /= 1024
            index += 1
        
        return f"{bytes_value:.2f} {suffixes[index]}"
    
    @staticmethod
    def calculate_file_size(width: int, height: int, format_name: str, seconds: float = 0.0) -> int:
        """
        Calculate approximate file size
        
        Args:
            width: Width
            height: Height
            format_name: Format name
            seconds: Duration in seconds (for video)
            
        Returns:
            Approximate size in bytes
        """
        format_name = format_name.upper()
        pixels = width * height
        
        if format_name == 'JPEG':
            # Assume 8:1 compression
            size = pixels * 3 / 8
        elif format_name == 'PNG':
            # Assume 2:1 compression
            size = pixels * 3 / 2
        elif format_name == 'RAW' or format_name == 'DNG':
            # Assume 12 bits per pixel
            size = pixels * 12 / 8
        elif format_name == 'YUV420':
            # 1.5 bytes per pixel
            size = pixels * 1.5
        elif format_name == 'RGB888':
            # 3 bytes per pixel
            size = pixels * 3
        elif format_name == 'H264' and seconds > 0:
            # Very rough estimate for H.264 video
            bitrate = 10000000  # 10 Mbps
            size = bitrate * seconds / 8
        else:
            # Default
            size = pixels * 3
        
        return int(size)
