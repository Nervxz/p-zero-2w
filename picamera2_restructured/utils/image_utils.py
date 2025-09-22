"""
ImageUtils - Image processing and manipulation utilities

This module provides utility functions for working with camera images, including
format conversions, transformations, and analysis.
"""

import numpy as np
import io
from typing import Union, Tuple, List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ExifTags
import time
import logging
import os
import math

# Setup logging
logger = logging.getLogger(__name__)


class ImageUtils:
    """
    Utility functions for image processing and manipulation
    """
    
    @staticmethod
    def array_to_image(array: np.ndarray) -> Image.Image:
        """
        Convert numpy array to PIL Image
        
        Args:
            array: Image array
            
        Returns:
            PIL Image
        """
        return Image.fromarray(array)
    
    @staticmethod
    def array_to_jpeg(array: np.ndarray, quality: int = 95) -> bytes:
        """
        Convert numpy array to JPEG bytes
        
        Args:
            array: Image array
            quality: JPEG quality (0-100)
            
        Returns:
            JPEG image bytes
        """
        image = Image.fromarray(array)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        return buffer.getvalue()
    
    @staticmethod
    def array_to_png(array: np.ndarray) -> bytes:
        """
        Convert numpy array to PNG bytes
        
        Args:
            array: Image array
            
        Returns:
            PNG image bytes
        """
        image = Image.fromarray(array)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    
    @staticmethod
    def image_to_array(image: Image.Image) -> np.ndarray:
        """
        Convert PIL Image to numpy array
        
        Args:
            image: PIL Image
            
        Returns:
            Image array
        """
        return np.array(image)
    
    @staticmethod
    def add_timestamp(image: Union[np.ndarray, Image.Image], format_str: str = "%Y-%m-%d %H:%M:%S",
                      position: str = "bottom-right", color: Tuple[int, int, int] = (255, 255, 255),
                      shadow: bool = True) -> Union[np.ndarray, Image.Image]:
        """
        Add timestamp to image
        
        Args:
            image: Input image (array or PIL Image)
            format_str: Time format string
            position: Text position ('top-left', 'top-right', 'bottom-left', 'bottom-right')
            color: Text color (RGB)
            shadow: Whether to add text shadow for better visibility
            
        Returns:
            Image with timestamp added
        """
        # Convert to PIL Image if needed
        is_array = isinstance(image, np.ndarray)
        if is_array:
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Create timestamp
        timestamp = time.strftime(format_str)
        
        # Create drawing context
        draw = ImageDraw.Draw(pil_image)
        
        # Try to load font, use default if not available
        font = None
        try:
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "C:\\Windows\\Fonts\\Arial.ttf"
            ]
            
            for path in font_paths:
                if os.path.exists(path):
                    font = ImageFont.truetype(path, 16)
                    break
        except Exception:
            pass
        
        # Get text size to position correctly
        text_width, text_height = draw.textbbox((0, 0), timestamp, font=font)[2:]
        
        # Determine position coordinates
        width, height = pil_image.size
        padding = 10
        
        if position == "top-left":
            x = padding
            y = padding
        elif position == "top-right":
            x = width - text_width - padding
            y = padding
        elif position == "bottom-left":
            x = padding
            y = height - text_height - padding
        else:  # bottom-right
            x = width - text_width - padding
            y = height - text_height - padding
        
        # Draw shadow for better visibility
        if shadow:
            shadow_color = (0, 0, 0)
            for dx, dy in [(1, 1), (1, 0), (0, 1)]:
                draw.text((x + dx, y + dy), timestamp, font=font, fill=shadow_color)
        
        # Draw text
        draw.text((x, y), timestamp, font=font, fill=color)
        
        # Return in original format
        if is_array:
            return np.array(pil_image)
        return pil_image
    
    @staticmethod
    def crop_center(image: Union[np.ndarray, Image.Image], width: int, height: int) -> Union[np.ndarray, Image.Image]:
        """
        Crop image to specified dimensions from center
        
        Args:
            image: Input image (array or PIL Image)
            width: Target width
            height: Target height
            
        Returns:
            Cropped image
        """
        # Convert to PIL Image if needed
        is_array = isinstance(image, np.ndarray)
        if is_array:
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Get dimensions
        img_width, img_height = pil_image.size
        
        # Calculate crop box
        left = (img_width - width) // 2
        top = (img_height - height) // 2
        right = left + width
        bottom = top + height
        
        # Ensure crop box is within image boundaries
        left = max(0, left)
        top = max(0, top)
        right = min(img_width, right)
        bottom = min(img_height, bottom)
        
        # Crop image
        cropped = pil_image.crop((left, top, right, bottom))
        
        # Return in original format
        if is_array:
            return np.array(cropped)
        return cropped
    
    @staticmethod
    def resize_image(image: Union[np.ndarray, Image.Image], width: int, height: int,
                     keep_aspect: bool = True) -> Union[np.ndarray, Image.Image]:
        """
        Resize image to specified dimensions
        
        Args:
            image: Input image (array or PIL Image)
            width: Target width
            height: Target height
            keep_aspect: Whether to maintain aspect ratio
            
        Returns:
            Resized image
        """
        # Convert to PIL Image if needed
        is_array = isinstance(image, np.ndarray)
        if is_array:
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        if keep_aspect:
            # Calculate new dimensions while preserving aspect ratio
            img_width, img_height = pil_image.size
            aspect_ratio = img_width / img_height
            
            if width / height > aspect_ratio:
                # Height is limiting factor
                new_height = height
                new_width = int(height * aspect_ratio)
            else:
                # Width is limiting factor
                new_width = width
                new_height = int(width / aspect_ratio)
            
            resized = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            # Resize to exact dimensions
            resized = pil_image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Return in original format
        if is_array:
            return np.array(resized)
        return resized
    
    @staticmethod
    def add_overlay_text(image: Union[np.ndarray, Image.Image], text: str, position: Tuple[int, int] = None,
                       color: Tuple[int, int, int] = (255, 255, 255), 
                       shadow: bool = True) -> Union[np.ndarray, Image.Image]:
        """
        Add text overlay to image
        
        Args:
            image: Input image (array or PIL Image)
            text: Text to add
            position: Text position (x, y), centered if None
            color: Text color (RGB)
            shadow: Whether to add text shadow for better visibility
            
        Returns:
            Image with text overlay
        """
        # Convert to PIL Image if needed
        is_array = isinstance(image, np.ndarray)
        if is_array:
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Create drawing context
        draw = ImageDraw.Draw(pil_image)
        
        # Try to load font, use default if not available
        font = None
        try:
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "C:\\Windows\\Fonts\\Arial.ttf"
            ]
            
            for path in font_paths:
                if os.path.exists(path):
                    font = ImageFont.truetype(path, 24)
                    break
        except Exception:
            pass
        
        # Get text size to position correctly
        text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
        
        # Determine position coordinates
        width, height = pil_image.size
        
        if position is None:
            x = (width - text_width) // 2
            y = (height - text_height) // 2
        else:
            x, y = position
        
        # Draw shadow for better visibility
        if shadow:
            shadow_color = (0, 0, 0)
            for dx, dy in [(2, 2), (2, 0), (0, 2)]:
                draw.text((x + dx, y + dy), text, font=font, fill=shadow_color)
        
        # Draw text
        draw.text((x, y), text, font=font, fill=color)
        
        # Return in original format
        if is_array:
            return np.array(pil_image)
        return pil_image
    
    @staticmethod
    def extract_exif_data(jpeg_bytes: bytes) -> Dict[str, Any]:
        """
        Extract EXIF metadata from JPEG image
        
        Args:
            jpeg_bytes: JPEG image bytes
            
        Returns:
            Dictionary with EXIF metadata
        """
        try:
            image = Image.open(io.BytesIO(jpeg_bytes))
            exif_data = {}
            
            if hasattr(image, '_getexif') and image._getexif():
                exif = image._getexif()
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
            
            return exif_data
        except Exception as e:
            logger.error(f"Failed to extract EXIF data: {e}")
            return {}
    
    @staticmethod
    def calculate_histogram(image: Union[np.ndarray, Image.Image], bins: int = 256) -> Dict[str, np.ndarray]:
        """
        Calculate image histogram
        
        Args:
            image: Input image
            bins: Number of bins
            
        Returns:
            Dictionary with histogram data for each channel
        """
        # Convert to numpy array if needed
        if not isinstance(image, np.ndarray):
            image_array = np.array(image)
        else:
            image_array = image
        
        # Determine image type and calculate histogram
        if len(image_array.shape) == 2:
            # Grayscale image
            hist, bins = np.histogram(image_array.flatten(), bins=bins, range=[0, 256])
            return {'gray': hist}
        elif len(image_array.shape) == 3 and image_array.shape[2] == 3:
            # RGB image
            hist_r, _ = np.histogram(image_array[:, :, 0].flatten(), bins=bins, range=[0, 256])
            hist_g, _ = np.histogram(image_array[:, :, 1].flatten(), bins=bins, range=[0, 256])
            hist_b, _ = np.histogram(image_array[:, :, 2].flatten(), bins=bins, range=[0, 256])
            return {'r': hist_r, 'g': hist_g, 'b': hist_b}
        else:
            # Unknown format
            logger.error("Unsupported image format for histogram calculation")
            return {}
    
    @staticmethod
    def yuv420_to_rgb(yuv_array: np.ndarray, width: int, height: int) -> np.ndarray:
        """
        Convert YUV420 array to RGB
        
        Args:
            yuv_array: YUV420 array
            width: Image width
            height: Image height
            
        Returns:
            RGB numpy array
        """
        try:
            from picamera2.converters import YUV420_to_RGB
            
            # Perform conversion
            rgb = YUV420_to_RGB(yuv_array, width, height)
            return rgb
        except Exception as e:
            logger.error(f"Failed to convert YUV420 to RGB: {e}")
            return np.zeros((height, width, 3), dtype=np.uint8)
    
    @staticmethod
    def adjust_brightness(image: Union[np.ndarray, Image.Image], factor: float) -> Union[np.ndarray, Image.Image]:
        """
        Adjust image brightness
        
        Args:
            image: Input image
            factor: Brightness factor (1.0 = original, > 1.0 = brighter, < 1.0 = darker)
            
        Returns:
            Adjusted image
        """
        # Convert to PIL Image if needed
        is_array = isinstance(image, np.ndarray)
        if is_array:
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Use ImageEnhance for brightness adjustment
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(pil_image)
        adjusted = enhancer.enhance(factor)
        
        # Return in original format
        if is_array:
            return np.array(adjusted)
        return adjusted
