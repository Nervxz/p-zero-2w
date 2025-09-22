# PiCamera2 Restructured - Quick Start Guide

This guide will help you quickly get up and running with the PiCamera2 Restructured library.

## Installation

1. Make sure you have the original picamera2 library installed:

```bash
sudo apt install -y python3-picamera2
```

2. Add the picamera2_restructured directory to your Python path:

```bash
# Add to your .bashrc or .bash_profile
export PYTHONPATH=$PYTHONPATH:/path/to/picamera2_restructured
```

## Basic Usage

### Take a Photo

```python
from picamera2_restructured import CameraController

# Initialize camera
camera = CameraController()
camera.initialize()

try:
    # Capture JPEG image
    image_data = camera.capture.capture_image()
    
    # Save to file
    with open('photo.jpg', 'wb') as f:
        f.write(image_data)
    
    print("Photo saved to photo.jpg")
finally:
    # Always close the camera
    camera.close()
```

### Show a Preview

```python
from picamera2_restructured import CameraController
import time

# Initialize camera
camera = CameraController()
camera.initialize()

try:
    # Start preview window
    camera.preview.start()
    
    # Keep preview open for 10 seconds
    print("Preview active for 10 seconds...")
    time.sleep(10)
finally:
    # Stop preview and close camera
    camera.preview.stop()
    camera.close()
```

### Record a Video

```python
from picamera2_restructured import CameraController
import time

# Initialize camera
camera = CameraController()
camera.initialize()

try:
    # Start preview window
    camera.preview.start()
    
    # Start recording
    camera.encoding.start_video_recording('video.mp4')
    
    # Record for 10 seconds
    print("Recording video for 10 seconds...")
    time.sleep(10)
    
    # Stop recording
    camera.encoding.stop_video_recording()
    print("Video saved to video.mp4")
finally:
    # Stop preview and close camera
    camera.preview.stop()
    camera.close()
```

## Capture Options

### Different Image Formats

```python
# JPEG format (default)
jpeg_image = camera.capture.capture_image(format='jpeg')

# PNG format
png_image = camera.capture.capture_image(format='png')

# Raw numpy array
array_image = camera.capture.capture_image(format='array')
```

### Adding Timestamp

```python
from picamera2_restructured.utils import ImageUtils

# Capture as array
image_array = camera.capture.capture_image(format='array')

# Add timestamp
timestamped = ImageUtils.add_timestamp(image_array)

# Convert to JPEG
jpeg_data = ImageUtils.array_to_jpeg(timestamped)

# Save to file
with open('timestamped.jpg', 'wb') as f:
    f.write(jpeg_data)
```

### Multiple Captures (Burst)

```python
# Capture 5 images with 0.5s interval
images = camera.capture.capture_burst(count=5, interval=0.5)

# Save images
for i, img in enumerate(images):
    with open(f"burst_{i}.jpg", 'wb') as f:
        f.write(img)
```

## Preview Options

### Qt Preview Window

```python
# Start Qt preview with custom size
camera.preview.start(
    preview_type='qt',
    width=800,
    height=600,
    window_title="My Camera"
)
```

### Null Preview (No Display)

```python
# Start null preview (processes frames but no visible output)
camera.preview.start(preview_type='null')
```

## Video Options

### Different Quality Settings

```python
# Low quality (smaller file size)
camera.encoding.start_video_recording('low_quality.mp4', quality='low')

# High quality
camera.encoding.start_video_recording('high_quality.mp4', quality='high')

# Custom bitrate
camera.encoding.start_video_recording('custom.mp4', bitrate=15000000)  # 15 Mbps
```

### Using Different Encoders

```python
# H.264 encoder (default)
camera.encoding.start_video_recording('h264_video.mp4', encoder_type='h264')

# MJPEG encoder
camera.encoding.start_video_recording('mjpeg_video.mp4', encoder_type='mjpeg')

# LibAV encoder (if available)
camera.encoding.start_video_recording('libav_video.mp4', encoder_type='libav')
```

## Utility Functions

```python
from picamera2_restructured.utils import ImageUtils, FormatUtils

# Resize image
resized = ImageUtils.resize_image(image, width=640, height=480)

# Add text overlay
with_text = ImageUtils.add_overlay_text(image, "Hello World", position=(50, 50))

# Check if format is supported
is_supported = FormatUtils.is_format_supported('JPEG')  # True

# Calculate aspect ratio
ratio = FormatUtils.calculate_aspect_ratio(1920, 1080)  # "16:9"
```

## Next Steps

- Explore the [USAGE.md](USAGE.md) guide for more detailed examples
- Check the [API_REFERENCE.md](API_REFERENCE.md) for complete API documentation
- Look at the [examples/](examples/) directory for sample code
