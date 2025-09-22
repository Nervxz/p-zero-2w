# PiCamera2 Utils Module

This module provides utility functions and helpers for working with camera data and formats.

## Overview

The utils module contains utility classes and functions that can be used across the library or by end users to work with camera data and formats.

## Utility Classes

### ImageUtils

Image processing and manipulation utilities:

- Format conversion (arrays, JPEG, PNG)
- Image transformation (resize, crop)
- Adding overlays (timestamps, text)
- Histogram calculation
- Color space conversion

```python
from picamera2_restructured.utils import ImageUtils

# Convert numpy array to JPEG bytes
jpeg_data = ImageUtils.array_to_jpeg(image_array)

# Add timestamp to image
timestamped_img = ImageUtils.add_timestamp(image)

# Resize image
resized_img = ImageUtils.resize_image(image, width=640, height=480)
```

### FormatUtils

Camera format and configuration utilities:

- Format checking and conversion
- Format-specific calculations
- Configuration formatting and display
- Human-readable conversions

```python
from picamera2_restructured.utils import FormatUtils

# Check if format is supported
is_jpeg_supported = FormatUtils.is_format_supported('JPEG')

# Get human-readable aspect ratio
aspect_ratio = FormatUtils.calculate_aspect_ratio(1920, 1080)  # Returns "16:9"

# Calculate file size for a given format and resolution
size_bytes = FormatUtils.calculate_file_size(1920, 1080, 'JPEG')
```

## Usage

These utilities can be used both internally by the library and directly by users who need to perform operations on camera data:

```python
from picamera2_restructured import CameraController
from picamera2_restructured.utils import ImageUtils

# Capture image
camera = CameraController()
camera.initialize()
image = camera.capture.capture_image(format='array')

# Process image using utilities
processed_image = ImageUtils.add_timestamp(image)
resized = ImageUtils.resize_image(processed_image, width=640, height=360)
jpeg_data = ImageUtils.array_to_jpeg(resized)

# Save processed image
with open('processed.jpg', 'wb') as f:
    f.write(jpeg_data)
```
