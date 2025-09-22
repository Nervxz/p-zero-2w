# PiCamera2 Services Module

This module provides specialized services for camera operations like capture, preview, and encoding.

## Overview

The services module contains specialized service classes that implement different aspects of camera functionality. These services are used by the high-level API classes to provide a clean, modular implementation.

## Service Categories

### Capture Services

Services for capturing images in various formats and configurations:

- `CaptureService`: Base service for image capture
- `ImageCapture`: Standard image capture (JPEG, PNG, etc.)
- `RawCapture`: RAW format image capture
- `BurstCapture`: Multi-image burst capture
- `TimelapseCapture`: Timelapse image sequences

```python
# These services are used internally by the CaptureAPI
# But can be accessed directly if needed
from picamera2_restructured.services.capture import ImageCapture

# Create service with a PiCamera2 instance
image_capture = ImageCapture(picam2)
jpeg_image = image_capture.capture(format='jpeg')
```

### Preview Services

Services for displaying camera preview in different ways:

- `PreviewService`: Base service for camera preview
- `QtPreview`: Qt-based window preview
- `DrmPreview`: DRM-based preview (direct rendering)
- `NullPreview`: Preview processing without display

```python
# These services are used internally by the PreviewAPI
from picamera2_restructured.services.preview import QtPreview

# Create service with a PiCamera2 instance
preview = QtPreview(picam2)
preview.start_preview(width=800, height=600)
```

### Encoding Services

Services for video recording and encoding:

- `EncodingService`: Base service for video encoding
- `H264Encoding`: H.264 video recording
- `MJPEGEncoding`: Motion JPEG video recording
- `LibavEncoding`: FFmpeg/LibAV-based encoding

```python
# These services are used internally by the EncodingAPI
from picamera2_restructured.services.encoding import H264Encoding

# Create service with a PiCamera2 instance
encoder = H264Encoding(picam2)
encoder.start_recording('video.mp4', bitrate=10000000)
```

## Internal Usage

These service components are primarily used internally by the API layer to implement the user-facing functionality in a modular, maintainable way. Each service focuses on a specific aspect of camera functionality.
