# PiCamera2 Restructured

A clean, modular, and easy-to-use API for the Raspberry Pi Camera.

## Overview

PiCamera2 Restructured reorganizes the powerful PiCamera2 library into a more accessible, modular structure with a focus on usability and maintainability. The library provides intuitive interfaces that make it simple to control your Raspberry Pi camera without having to understand the complex underlying codebase.

This restructured version is designed with a clear separation of concerns:
- High-level **API classes** provide simple access for common tasks
- Specialized **service modules** implement specific functionality
- **Core components** handle the fundamental camera operations
- **Device-specific modules** optimize for different camera hardware
- **Utility functions** make working with camera data easier

## Key Features

- **Simple API**: Intuitive methods for all camera operations
- **Modular Design**: Clean separation of functionality into logical components
- **Device Support**: Optimized for different camera modules (IMX708, IMX500, etc.)
- **Specialized AI Integration**: Support for IMX500 vision sensor with object detection
- **Advanced Services**: Comprehensive capture, preview, and encoding capabilities
- **Powerful Utilities**: Image processing and format handling tools
- **Well-documented**: Clear examples and detailed API documentation
- **Compatible**: Built on top of the standard PiCamera2 library
- **Extensible**: Easy to add new device support or functionality

## Installation

1. Ensure you have the original picamera2 library installed:

```bash
sudo apt install -y python3-picamera2
```

2. Clone this repository:

```bash
git clone https://github.com/yourusername/picamera2_restructured.git
```

3. Add to your Python path or install locally:

```bash
# Option 1: Add to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:/path/to/picamera2_restructured

# Option 2: Install locally
cd picamera2_restructured
pip install -e .
```

## Quick Start

```python
from picamera2_restructured import CameraController

# Initialize camera
camera = CameraController()
camera.initialize()

# Capture an image
image_data = camera.capture.capture_image(format='jpeg')
with open('image.jpg', 'wb') as f:
    f.write(image_data)

# Start a preview
camera.preview.start()

# Record video
camera.encoding.start_video_recording('video.mp4')
# Wait or perform other tasks...
camera.encoding.stop_video_recording()

# Clean up
camera.close()
```

## Module Structure

The library is organized into a clear, modular structure:

- **api/**: High-level interfaces for camera operations
  - `camera_controller.py` - Main entry point for camera control
  - `capture_api.py` - Image capture interface
  - `preview_api.py` - Preview management interface
  - `encoding_api.py` - Video recording interface

- **core/**: Core implementation and configurations
  - `camera_core.py` - Base camera implementation
  - `configuration_manager.py` - Camera configuration handling

- **devices/**: Device-specific implementations
  - `device_manager.py` - Manages camera devices
  - `base_device.py` - Base device class
  - **imx708/** - Raspberry Pi Camera Module 3 support
  - **imx500/** - Sony IMX500 intelligent vision sensor support
  - **hailo/** - Hailo AI accelerator support

- **interfaces/**: Interface definitions
  - `camera_interface.py` - Camera interface definition
  - `device_interface.py` - Device interface definition

- **services/**: Service modules implementation
  - **capture/** - Image capture services (standard, raw, burst, timelapse)
  - **preview/** - Camera preview services (Qt, DRM, null)
  - **encoding/** - Video encoding services (H.264, MJPEG, LibAV)

- **utils/**: Utility functions
  - `image_utils.py` - Image processing utilities
  - `format_utils.py` - Format handling utilities

- **examples/**: Usage examples and sample code
  - Basic camera operations examples
  - **imx500/** - Specialized examples for IMX500 object detection

For a complete file-by-file breakdown, see [MODULE_STRUCTURE.md](MODULE_STRUCTURE.md)

## Examples

The `examples/` directory contains several scripts demonstrating different features:

- **basic_capture.py**: Simple image capture
- **preview_and_capture.py**: Preview window with capture
- **video_recording.py**: Video recording with preview
- **timelapse.py**: Capture a sequence of images over time
- **advanced_capture.py**: Advanced capture techniques

### IMX500 Examples

The `examples/imx500/` directory contains specialized examples for the Sony IMX500 intelligent vision sensor:

- **object_detection_demo.py**: Full object detection demo with multi-threading
- **simple_detection.py**: Simple object detection implementation

To run an example:

```bash
cd picamera2_restructured
python examples/basic_capture.py

# For IMX500 object detection
python examples/imx500/simple_detection.py --model /path/to/model.rpk --labels /path/to/labels.txt
```

## API Overview

### CameraController

The main entry point for all camera operations:

```python
camera = CameraController()
camera.initialize()
```

### Image Capture

```python
# Basic JPEG capture
jpeg_data = camera.capture.capture_image()

# Capture RAW format
raw_data = camera.capture.capture_raw()

# Capture with timestamp
jpeg_with_timestamp = camera.capture.capture_image_with_timestamp()

# Burst capture
images = camera.capture.capture_burst(count=5, interval=0.5)
```

### Preview

```python
# Start default preview
camera.preview.start()

# Start Qt preview window with size
camera.preview.start(preview_type='qt', width=800, height=600)

# Start DRM preview (direct rendering)
camera.preview.start(preview_type='drm')

# Stop preview
camera.preview.stop()
```

### Video Recording

```python
# Start recording with default settings
camera.encoding.start_video_recording('video.mp4')

# Start recording with high quality and 60fps
camera.encoding.start_video_recording(
    'hq_video.mp4',
    quality='high',
    fps=60
)

# Stop recording
camera.encoding.stop_video_recording()
```

## Advanced Usage

### Custom Configurations

```python
# Get recommended configuration for current device
config = camera.native.create_still_configuration(
    main={"size": (4056, 3040)},
    lores={"size": (640, 480)},
    display="lores"
)

# Apply configuration
camera.configure(config)
```

### Using Utilities

```python
from picamera2_restructured.utils import ImageUtils

# Convert array to JPEG bytes
jpeg_data = ImageUtils.array_to_jpeg(image_array)

# Add timestamp overlay
timestamped_img = ImageUtils.add_timestamp(image)

# Resize image
resized_img = ImageUtils.resize_image(image, width=640, height=480)
```

## Accessing Original PiCamera2

For advanced features not yet covered by the restructured API:

```python
# Access the underlying PiCamera2 instance
picam2 = camera.native

# Use native methods directly
picam2.capture_file("image.jpg")
```

## Documentation

- [API Reference](API_REFERENCE.md): Detailed API documentation
- [Usage Guide](USAGE.md): Comprehensive usage examples
- [Quick Start Guide](QUICKSTART.md): Get up and running quickly
- [Module Structure](MODULE_STRUCTURE.md): Complete package structure overview
- [SUMMARY.md](SUMMARY.md): Library design and architecture overview

Each module directory also contains its own README.md with specific documentation:
- [API Documentation](api/README.md)
- [Core Documentation](core/README.md)
- [Devices Documentation](devices/README.md)
- [Interfaces Documentation](interfaces/README.md)
- [Services Documentation](services/README.md)
- [Utilities Documentation](utils/README.md)
- [Examples Documentation](examples/README.md)
- [IMX500 Examples Documentation](examples/imx500/README.md)

## License

Same as the original PiCamera2 library.

## Credits

Based on the official [PiCamera2](https://github.com/raspberrypi/picamera2) library.