# PiCamera2 Restructured - Usage Guide

This guide provides comprehensive examples of how to use the PiCamera2 Restructured library for various camera operations.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Image Capture](#basic-image-capture)
3. [Camera Preview](#camera-preview)
4. [Video Recording](#video-recording)
5. [Advanced Capture Techniques](#advanced-capture-techniques)
6. [Working with Images](#working-with-images)
7. [Device-Specific Features](#device-specific-features)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

Ensure you have the original picamera2 library installed:

```bash
sudo apt install -y python3-picamera2
```

Add the picamera2_restructured directory to your Python path or install it locally.

### Basic Initialization

```python
from picamera2_restructured import CameraController

# Initialize camera
camera = CameraController()
camera.initialize()

# Always close the camera when done
camera.close()
```

### Using with Context Manager

```python
from picamera2_restructured import CameraController

# Use context manager to ensure proper cleanup
with CameraController() as camera:
    camera.initialize()
    # Your code here...
    # Camera is automatically closed when exiting the with block
```

## Basic Image Capture

### Capture JPEG Image

```python
# Capture JPEG image
jpeg_data = camera.capture.capture_image(format='jpeg')

# Save to file
with open('image.jpg', 'wb') as f:
    f.write(jpeg_data)
```

### Capture PNG Image

```python
# Capture PNG image
png_data = camera.capture.capture_image(format='png')

# Save to file
with open('image.png', 'wb') as f:
    f.write(png_data)
```

### Capture to File Directly

```python
# Capture directly to file
camera.capture.capture_to_file('image.jpg')
```

### Capture Array for Processing

```python
# Capture as numpy array for image processing
array = camera.capture.capture_image(format='array')

# Process with PIL
from PIL import Image, ImageFilter
img = Image.fromarray(array)
blurred = img.filter(ImageFilter.BLUR)
blurred.save('blurred.jpg')
```

## Camera Preview

### Start Default Preview

```python
# Start preview (default type depends on platform)
camera.preview.start()
```

### Qt Preview Window

```python
# Start Qt preview window
camera.preview.start(
    preview_type='qt',
    width=800,
    height=600,
    window_title="Camera Preview"
)
```

### DRM Preview (Direct Rendering)

```python
# Start DRM preview (for direct rendering on Raspberry Pi)
camera.preview.start(preview_type='drm')
```

### Null Preview (Processing Without Display)

```python
# Start null preview (no visible output, but processes frames)
camera.preview.start(preview_type='null')
```

### Stopping Preview

```python
# Stop preview
camera.preview.stop()
```

## Video Recording

### Basic Video Recording

```python
# Start recording
camera.encoding.start_video_recording('video.mp4')

# Record for 10 seconds
import time
time.sleep(10)

# Stop recording
camera.encoding.stop_video_recording()
```

### Recording with Quality Settings

```python
# Record high quality video
camera.encoding.start_video_recording(
    'high_quality.mp4',
    quality='high',
    fps=30
)

# Record with specific bitrate
camera.encoding.start_video_recording(
    'custom_bitrate.mp4',
    bitrate=15000000  # 15 Mbps
)
```

### Recording with Duration

```python
# Record for specific duration
camera.encoding.start_video_recording(
    'timed_video.mp4',
    duration=5.0  # Will automatically stop after 5 seconds
)
```

### Pause and Resume Recording

```python
# Start recording
camera.encoding.start_video_recording('video_with_pause.mp4')

# Record for 3 seconds
time.sleep(3)

# Pause recording
camera.encoding.pause_recording()
print("Recording paused")

# Wait 2 seconds
time.sleep(2)

# Resume recording
camera.encoding.resume_recording()
print("Recording resumed")

# Record 3 more seconds
time.sleep(3)

# Stop recording
camera.encoding.stop_video_recording()
```

## Advanced Capture Techniques

### Capture with Metadata

```python
# Capture image with metadata
image, metadata = camera.capture.capture_with_metadata()

# Print some metadata
print(f"Exposure time: {metadata.get('ExposureTime')} μs")
print(f"Analog gain: {metadata.get('AnalogueGain')}")
```

### Burst Capture

```python
# Capture burst of 5 images
images = camera.capture.capture_burst(count=5, interval=0.5)

# Save images
for i, img in enumerate(images):
    with open(f"burst_{i}.jpg", 'wb') as f:
        f.write(img)
```

### Timelapse Capture

```python
# Capture timelapse sequence
camera.capture.capture_timelapse(
    count=60,            # Number of images
    interval=10,         # Seconds between captures
    output_dir="timelapse_output"
)
```

### Capture with Custom Configuration

```python
# Create custom configuration
config = {
    'main': {'size': (4056, 3040)},  # Max resolution
    'lores': {'size': (640, 480)},   # Preview resolution
    'controls': {
        'FrameRate': 15.0,           # Lower framerate for higher quality
        'AwbEnable': True,           # Auto white balance
        'AeEnable': True             # Auto exposure
    }
}

# Apply configuration
camera.configure(config)

# Capture with this configuration
high_res_image = camera.capture.capture_image()
```

## Working with Images

### Adding Timestamp

```python
from picamera2_restructured.utils import ImageUtils

# Capture image
image = camera.capture.capture_image(format='array')

# Add timestamp
timestamped = ImageUtils.add_timestamp(
    image,
    format_str="%Y-%m-%d %H:%M:%S",
    position="bottom-right"
)

# Convert to JPEG and save
jpeg_data = ImageUtils.array_to_jpeg(timestamped)
with open('timestamped.jpg', 'wb') as f:
    f.write(jpeg_data)
```

### Image Resizing

```python
from picamera2_restructured.utils import ImageUtils

# Capture image
image = camera.capture.capture_image(format='array')

# Resize image
resized = ImageUtils.resize_image(image, width=640, height=360)

# Convert to JPEG and save
jpeg_data = ImageUtils.array_to_jpeg(resized)
with open('resized.jpg', 'wb') as f:
    f.write(jpeg_data)
```

### Adding Text Overlay

```python
from picamera2_restructured.utils import ImageUtils

# Capture image
image = camera.capture.capture_image(format='array')

# Add text overlay
with_text = ImageUtils.add_overlay_text(
    image,
    "Hello from Raspberry Pi",
    position=(50, 50),
    color=(255, 255, 0)  # Yellow text
)

# Convert to JPEG and save
jpeg_data = ImageUtils.array_to_jpeg(with_text)
with open('with_text.jpg', 'wb') as f:
    f.write(jpeg_data)
```

### Color Space Conversion

```python
from picamera2_restructured.utils import ImageUtils

# Convert YUV420 to RGB
rgb_image = ImageUtils.yuv420_to_rgb(yuv_data, width, height)
```

## Device-Specific Features

### Working with IMX708 (Raspberry Pi Camera Module 3)

```python
from picamera2_restructured import CameraController
from picamera2_restructured.devices import DeviceManager

# Initialize device manager
manager = DeviceManager()

# Detect available devices
devices = manager.detect_devices()
print(f"Detected devices: {devices}")

# Initialize camera controller
camera = CameraController()
camera.initialize()

# Get camera information
info = camera.camera_info
if 'IMX708' in info.get('camera_name', ''):
    print("Using Raspberry Pi Camera Module 3")
    
    # Get recommended configuration for IMX708
    config = camera.native.create_still_configuration(
        main={"size": (4608, 2592)},  # Max resolution for IMX708
    )
    camera.configure(config)
```

### Working with IMX500 (Intelligent Vision Sensor)

#### Basic IMX500 Usage

```python
from picamera2_restructured import CameraController
from picamera2_restructured.devices import DeviceManager
from picamera2_restructured.devices.imx500 import IMX500Device

# Initialize device manager
manager = DeviceManager()

# Get IMX500 device if available
imx500 = manager.initialize_device("camera0", "imx500")

if imx500:
    # Load AI model (if supported)
    imx500.load_ai_model("efficientdet")
    imx500.enable_ai_processing()
    
    # Initialize camera with this device
    camera = CameraController()
    camera.initialize()
    
    # Capture an image
    image = camera.capture.capture_image(format='array')
    
    # Process with IMX500 AI capabilities
    results = imx500.process_frame(image)
    print(f"Detection results: {results}")
```

#### IMX500 Object Detection

The library includes a full example for IMX500 object detection in `examples/imx500/object_detection_demo.py`. 
This example is equivalent to the original `imx500_object_detection_demo_mp.py` script but uses the restructured API.

To use the object detection demo:

```bash
cd picamera2_restructured
python examples/imx500/object_detection_demo.py --model /path/to/model.rpk --labels /path/to/labels.txt --fps 25 --bbox-normalization --ignore-dash-labels
```

Command line options:
- `--model`: Path to the model file (.rpk)
- `--labels`: Path to the labels file
- `--fps`: Frames per second (default: 25)
- `--display-width`: Display width (default: 640)
- `--display-height`: Display height (default: 480)
- `--threshold`: Detection threshold (default: 0.5)
- `--bbox-normalization`: Use normalized bounding box coordinates
- `--ignore-dash-labels`: Ignore labels starting with '-'

The object detection demo uses multi-threading to optimize performance:
1. A capture thread continuously captures frames from the camera
2. A processing thread runs the IMX500 AI model on the captured frames
3. A display thread shows the results with bounding boxes and labels

## Troubleshooting

### Common Issues

#### Camera Not Found

```python
try:
    camera = CameraController()
    camera.initialize()
except Exception as e:
    print(f"Camera initialization failed: {e}")
    print("Make sure the camera module is connected and enabled")
    # Check if camera is enabled in raspi-config
```

#### Preview Not Working

```python
# Try different preview types
try:
    camera.preview.start(preview_type='qt')
except Exception as e:
    print(f"Qt preview failed: {e}")
    try:
        print("Trying DRM preview...")
        camera.preview.start(preview_type='drm')
    except Exception as e:
        print(f"DRM preview also failed: {e}")
        print("Falling back to null preview")
        camera.preview.start(preview_type='null')
```

#### Memory Issues

```python
# For low memory devices, use smaller resolutions
camera.configure({
    'main': {'size': (1280, 720)},  # Lower resolution
    'lores': {'size': (320, 180)}   # Small preview
})
```
