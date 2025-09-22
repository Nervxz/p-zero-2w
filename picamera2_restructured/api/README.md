# PiCamera2 API Module

This module provides high-level, user-friendly interfaces for controlling the Raspberry Pi camera.

## Overview

The API module is the main entry point for most users, offering intuitive classes for camera control and operations without requiring deep knowledge of the underlying implementation.

## Key Components

### CameraController

The main API class that provides access to all camera functionality:

```python
from picamera2_restructured import CameraController

# Initialize the camera
camera = CameraController()
camera.initialize()

# Get camera information
info = camera.camera_info
print(f"Camera: {info.get('camera_name')}")

# Close the camera when done
camera.close()
```

### CaptureAPI

Handles image capture in various formats:

```python
# Access via the camera controller
jpeg_image = camera.capture.capture_image(format='jpeg')
raw_image = camera.capture.capture_raw()
```

### PreviewAPI

Manages camera preview functionality:

```python
# Start a preview window
camera.preview.start(preview_type='qt', width=800, height=600)

# Stop the preview
camera.preview.stop()
```

### EncodingAPI

Provides video recording capabilities:

```python
# Record a video
camera.encoding.start_video_recording('video.mp4', quality='high')
time.sleep(5)  # Record for 5 seconds
camera.encoding.stop_video_recording()
```

## Usage Examples

See the examples directory for complete usage examples.
