"""
Image optimization utilities.

This module provides utilities for optimizing image processing operations
using vectorized operations and other performance enhancements.
"""

import numpy as np
import cv2
from typing import Tuple, List, Dict, Any, Optional, Union
from functools import lru_cache

from .memory_utils import reduce_memory_usage, memory_pool
from .cache_utils import memoize

def optimize_image(image):
    """
    Optimize an image for processing.
    
    Args:
        image: Input image
        
    Returns:
        Optimized image
    """
    # Convert to numpy array if not already
    if not isinstance(image, np.ndarray):
        image = np.array(image)
    
    # Reduce memory usage by using a more efficient data type
    return reduce_memory_usage(image)

def fast_resize(image, size, interpolation=cv2.INTER_LINEAR):
    """
    Fast image resize using optimized operations.
    
    Args:
        image: Input image
        size: Target size as (width, height)
        interpolation: Interpolation method
        
    Returns:
        Resized image
    """
    # Use pre-allocated buffer for output if possible
    try:
        output_shape = (size[1], size[0]) + image.shape[2:]
        output = memory_pool.get(output_shape, image.dtype)
        cv2.resize(image, size, dst=output, interpolation=interpolation)
        return output
    except (ValueError, TypeError, cv2.error):
        # Fall back to standard resize
        return cv2.resize(image, size, interpolation=interpolation)

def fast_convert_color(image, conversion_code):
    """
    Fast color conversion using optimized operations.
    
    Args:
        image: Input image
        conversion_code: OpenCV color conversion code
        
    Returns:
        Converted image
    """
    # Determine output channels
    if conversion_code in [cv2.COLOR_BGR2GRAY, cv2.COLOR_RGB2GRAY]:
        output_shape = image.shape[:2]
        output_dtype = image.dtype
    elif conversion_code in [cv2.COLOR_GRAY2BGR, cv2.COLOR_GRAY2RGB]:
        output_shape = image.shape + (3,)
        output_dtype = image.dtype
    else:
        # For other conversions, let OpenCV handle it
        return cv2.cvtColor(image, conversion_code)
    
    # Use pre-allocated buffer for output if possible
    try:
        output = memory_pool.get(output_shape, output_dtype)
        cv2.cvtColor(image, conversion_code, dst=output)
        return output
    except (ValueError, TypeError, cv2.error):
        # Fall back to standard conversion
        return cv2.cvtColor(image, conversion_code)

@lru_cache(maxsize=32)
def get_gaussian_kernel(ksize, sigma):
    """
    Get a cached Gaussian kernel.
    
    Args:
        ksize: Kernel size
        sigma: Sigma value
        
    Returns:
        Gaussian kernel
    """
    return cv2.getGaussianKernel(ksize, sigma)

def fast_gaussian_blur(image, ksize, sigma):
    """
    Fast Gaussian blur using optimized operations.
    
    Args:
        image: Input image
        ksize: Kernel size
        sigma: Sigma value
        
    Returns:
        Blurred image
    """
    # Get cached kernel
    kernel = get_gaussian_kernel(ksize, sigma)
    
    # Use separable convolution for faster processing
    temp = cv2.sepFilter2D(image, -1, kernel, kernel.T)
    
    return temp

def vectorized_histogram(image, bins=256, range=(0, 256)):
    """
    Compute histogram using vectorized operations.
    
    Args:
        image: Input image
        bins: Number of bins
        range: Range of values
        
    Returns:
        Histogram
    """
    # Flatten the image
    flat_image = image.ravel()
    
    # Compute histogram using numpy
    hist, _ = np.histogram(flat_image, bins=bins, range=range)
    
    return hist

def fast_threshold(image, threshold, max_value=255, type=cv2.THRESH_BINARY):
    """
    Fast thresholding using vectorized operations.
    
    Args:
        image: Input image
        threshold: Threshold value
        max_value: Maximum value
        type: Threshold type
        
    Returns:
        Thresholded image
    """
    if type == cv2.THRESH_BINARY:
        return np.where(image > threshold, max_value, 0).astype(image.dtype)
    elif type == cv2.THRESH_BINARY_INV:
        return np.where(image > threshold, 0, max_value).astype(image.dtype)
    elif type == cv2.THRESH_TRUNC:
        return np.minimum(image, threshold).astype(image.dtype)
    elif type == cv2.THRESH_TOZERO:
        return np.where(image > threshold, image, 0).astype(image.dtype)
    elif type == cv2.THRESH_TOZERO_INV:
        return np.where(image > threshold, 0, image).astype(image.dtype)
    else:
        # Fall back to OpenCV for other types
        _, thresholded = cv2.threshold(image, threshold, max_value, type)
        return thresholded

def batch_process_images(images, process_func, batch_size=4):
    """
    Process a batch of images with a single function call.
    
    Args:
        images: List of input images
        process_func: Processing function
        batch_size: Size of each batch
        
    Returns:
        List of processed images
    """
    # Process images in batches
    results = []
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]
        batch_results = process_func(batch)
        results.extend(batch_results)
    
    return results

def optimize_bounding_boxes(boxes, image_shape):
    """
    Optimize bounding boxes for display.
    
    Args:
        boxes: List of bounding boxes as [x1, y1, x2, y2]
        image_shape: Shape of the image as (height, width)
        
    Returns:
        Optimized bounding boxes
    """
    # Convert to numpy array for vectorized operations
    if not isinstance(boxes, np.ndarray):
        boxes = np.array(boxes)
    
    # Ensure boxes are within image boundaries
    height, width = image_shape[:2]
    boxes[:, 0] = np.clip(boxes[:, 0], 0, width - 1)
    boxes[:, 1] = np.clip(boxes[:, 1], 0, height - 1)
    boxes[:, 2] = np.clip(boxes[:, 2], 0, width - 1)
    boxes[:, 3] = np.clip(boxes[:, 3], 0, height - 1)
    
    return boxes

def draw_optimized_boxes(image, boxes, labels=None, colors=None, thickness=2):
    """
    Draw bounding boxes on an image with optimized operations.
    
    Args:
        image: Input image
        boxes: List of bounding boxes as [x1, y1, x2, y2]
        labels: List of labels for each box
        colors: List of colors for each box
        thickness: Line thickness
        
    Returns:
        Image with bounding boxes
    """
    # Make a copy of the image to avoid modifying the original
    result = image.copy()
    
    # Default color if not provided
    default_color = (0, 255, 0)
    
    # Draw each box
    for i, box in enumerate(boxes):
        # Get coordinates
        x1, y1, x2, y2 = [int(coord) for coord in box]
        
        # Get color for this box
        color = colors[i] if colors and i < len(colors) else default_color
        
        # Draw rectangle
        cv2.rectangle(result, (x1, y1), (x2, y2), color, thickness)
        
        # Draw label if provided
        if labels and i < len(labels):
            label = labels[i]
            cv2.putText(result, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)
    
    return result

@memoize(maxsize=64)
def compute_image_features(image_data, algorithm='orb'):
    """
    Compute image features with caching.
    
    Args:
        image_data: Image data as bytes
        algorithm: Feature detection algorithm
        
    Returns:
        Image features
    """
    # Convert image data to numpy array
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Detect features
    if algorithm.lower() == 'orb':
        detector = cv2.ORB_create()
    elif algorithm.lower() == 'sift':
        detector = cv2.SIFT_create()
    else:
        detector = cv2.ORB_create()
    
    # Compute keypoints and descriptors
    keypoints, descriptors = detector.detectAndCompute(image, None)
    
    return keypoints, descriptors
