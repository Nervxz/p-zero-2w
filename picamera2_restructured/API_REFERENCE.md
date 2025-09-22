# PiCamera2 Restructured - API Reference

This document provides a detailed reference for the PiCamera2 Restructured API.

## Table of Contents

- [CameraController](#cameracontroller)
- [CaptureAPI](#captureapi)
- [PreviewAPI](#previewapi)
- [EncodingAPI](#encodingapi)
- [Utility Classes](#utility-classes)
- [Device Classes](#device-classes)

## CameraController

The main entry point for camera operations.

### Initialization

```python
from picamera2_restructured import CameraController

# Create controller for default camera (camera 0)
camera = CameraController()

# Create controller for specific camera
camera = CameraController(camera_num=1)

# Initialize camera
camera.initialize()
```

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `initialize()` | Initialize the camera | None | `bool`: True if successful |
| `configure(config=None)` | Configure camera with settings | `config` (dict, optional): Configuration dictionary | `bool`: True if successful |
| `start()` | Start camera | None | `bool`: True if successful |
| `stop()` | Stop camera | None | `bool`: True if successful |
| `close()` | Release camera resources | None | `bool`: True if successful |
| `get_controls()` | Get camera control settings | None | `dict`: Camera controls |
| `set_control(control, value)` | Set camera control | `control` (str): Control name<br>`value`: Control value | `bool`: True if successful |
| `get_all_data()` | Get all camera data | None | `dict`: All camera data |
| `get_all_data_json()` | Get all camera data as JSON | None | `str`: JSON string |

### Properties

| Property | Description | Type |
|----------|-------------|------|
| `camera_info` | Get camera information | `dict` |
| `is_initialized` | Check if camera is initialized | `bool` |
| `capture` | Access capture API | `CaptureAPI` |
| `preview` | Access preview API | `PreviewAPI` |
| `encoding` | Access encoding API | `EncodingAPI` |
| `native` | Access underlying Picamera2 instance | `Picamera2` |

### Context Manager

```python
with CameraController() as camera:
    camera.initialize()
    # Your code here
    # Camera will be automatically closed
```

## CaptureAPI

Handles image capture functionality.

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `capture_image(format='jpeg', **kwargs)` | Capture image | `format` (str): Image format ('jpeg', 'png', 'array', etc.)<br>`**kwargs`: Additional capture parameters | Image data (bytes or numpy array) |
| `capture_raw(**kwargs)` | Capture raw image | `**kwargs`: Additional capture parameters | Raw image data as numpy array |
| `capture_with_metadata(format='jpeg')` | Capture image with metadata | `format` (str): Image format | Tuple of (image data, metadata dict) |
| `capture_burst(count=5, interval=0.0, format='jpeg')` | Capture burst of images | `count` (int): Number of images<br>`interval` (float): Time between captures<br>`format` (str): Image format | List of images |
| `capture_to_file(file_path, format=None)` | Capture directly to file | `file_path` (str): Path to save file<br>`format` (str): Image format | `bool`: True if successful |
| `capture_continuous(count, interval=1.0, callback=None)` | Continuous capture with callback | `count` (int): Number of images<br>`interval` (float): Time between captures<br>`callback` (callable): Function to call with each image | List of images (if no callback) |

## PreviewAPI

Manages camera preview functionality.

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `start(preview_type='default', **kwargs)` | Start preview | `preview_type` (str): Type of preview ('qt', 'drm', 'null', etc.)<br>`**kwargs`: Additional preview parameters | `bool`: True if successful |
| `start_qt(x=100, y=100, width=640, height=480, window_title='Camera Preview')` | Start Qt preview window | Parameters for window position and size | `bool`: True if successful |
| `start_null()` | Start null preview (no visible output) | None | `bool`: True if successful |
| `start_drm()` | Start DRM preview (direct rendering) | None | `bool`: True if successful |
| `stop()` | Stop active preview | None | `bool`: True if successful |
| `configure(width=None, height=None, **kwargs)` | Configure preview | `width` (int): Preview width<br>`height` (int): Preview height<br>`**kwargs`: Additional parameters | `bool`: True if successful |

### Properties

| Property | Description | Type |
|----------|-------------|------|
| `is_active` | Check if preview is active | `bool` |
| `preview_type` | Get current preview type | `str` |
| `preview_config` | Get current preview configuration | `dict` |

## EncodingAPI

Provides video recording capabilities.

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `start_video_recording(output_file, quality=None, fps=None, bitrate=None, encoder_type=None, duration=None, **kwargs)` | Start video recording | `output_file` (str): Path to save video<br>`quality` (str): 'low', 'medium', 'high'<br>`fps` (int): Frames per second<br>`bitrate` (int): Encoding bitrate<br>`encoder_type` (str): 'h264', 'mjpeg', 'libav'<br>`duration` (float): Recording duration<br>`**kwargs`: Additional parameters | `bool`: True if successful |
| `stop_video_recording()` | Stop video recording | None | `bool`: True if successful |
| `pause_recording()` | Pause video recording | None | `bool`: True if successful |
| `resume_recording()` | Resume paused recording | None | `bool`: True if successful |
| `capture_while_recording(output_file)` | Capture still image during recording | `output_file` (str): Path to save image | `bool`: True if successful |
| `configure_encoding(config)` | Configure encoding settings | `config` (dict): Encoding configuration | `bool`: True if successful |
| `set_quality(quality)` | Set recording quality | `quality` (str): 'low', 'medium', 'high' | `bool`: True if successful |

### Properties

| Property | Description | Type |
|----------|-------------|------|
| `is_recording` | Check if currently recording | `bool` |
| `recording_file` | Get current recording file path | `str` |
| `encoding_config` | Get current encoding configuration | `dict` |

## Utility Classes

### ImageUtils

Static utility methods for image processing.

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `array_to_image(array)` | Convert numpy array to PIL Image | `array`: Image array | PIL Image |
| `array_to_jpeg(array, quality=95)` | Convert numpy array to JPEG bytes | `array`: Image array<br>`quality` (int): JPEG quality | JPEG bytes |
| `array_to_png(array)` | Convert numpy array to PNG bytes | `array`: Image array | PNG bytes |
| `image_to_array(image)` | Convert PIL Image to numpy array | `image`: PIL Image | Numpy array |
| `add_timestamp(image, format_str="%Y-%m-%d %H:%M:%S", position="bottom-right", color=(255,255,255), shadow=True)` | Add timestamp to image | `image`: Input image<br>Parameters for timestamp format and appearance | Image with timestamp |
| `crop_center(image, width, height)` | Crop image to dimensions from center | `image`: Input image<br>`width` (int): Target width<br>`height` (int): Target height | Cropped image |
| `resize_image(image, width, height, keep_aspect=True)` | Resize image | `image`: Input image<br>`width` (int): Target width<br>`height` (int): Target height<br>`keep_aspect` (bool): Maintain aspect ratio | Resized image |
| `add_overlay_text(image, text, position=None, color=(255,255,255), shadow=True)` | Add text overlay to image | `image`: Input image<br>`text` (str): Text to add<br>Parameters for text appearance | Image with text |
| `extract_exif_data(jpeg_bytes)` | Extract EXIF metadata from JPEG | `jpeg_bytes`: JPEG image bytes | Dict with EXIF data |
| `calculate_histogram(image, bins=256)` | Calculate image histogram | `image`: Input image<br>`bins` (int): Number of histogram bins | Dict with histogram data |
| `yuv420_to_rgb(yuv_array, width, height)` | Convert YUV420 array to RGB | `yuv_array`: YUV image data<br>`width` (int): Image width<br>`height` (int): Image height | RGB numpy array |

### FormatUtils

Static utility methods for format handling.

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `get_supported_formats()` | Get list of supported image formats | None | List of format names |
| `is_format_supported(format_name)` | Check if format is supported | `format_name` (str): Format to check | `bool`: True if supported |
| `get_pixel_format(format_name)` | Get libcamera pixel format | `format_name` (str): Format name | Pixel format string |
| `guess_file_format(filename)` | Guess format from filename extension | `filename` (str): Filename to check | Format name |
| `get_optimal_buffer_size(width, height, format_name)` | Calculate optimal buffer size | `width` (int): Image width<br>`height` (int): Image height<br>`format_name` (str): Format name | Buffer size in bytes |
| `calculate_aspect_ratio(width, height)` | Calculate aspect ratio as string | `width` (int): Width<br>`height` (int): Height | String like "16:9" |

## Device Classes

### DeviceManager

Manages camera devices and hardware accelerators.

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `detect_devices()` | Detect available camera devices | None | Dict of detected devices |
| `initialize_device(device_name, device_type=None)` | Initialize a device | `device_name` (str): Device name<br>`device_type` (str, optional): Device type | Initialized device or None |
| `get_device(device_name)` | Get initialized device | `device_name` (str): Device name | Device or None |
| `release_device(device_name)` | Release device resources | `device_name` (str): Device name | `bool`: True if successful |
| `release_all_devices()` | Release all device resources | None | None |
| `get_available_device_types()` | Get list of available device types | None | List of device type names |

### IMX708Device (Raspberry Pi Camera Module 3)

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `get_recommended_configuration()` | Get recommended configuration | None | Configuration dict |
| `get_hdr_configuration()` | Get HDR mode configuration | None | Configuration dict |
| `get_low_light_configuration()` | Get low-light configuration | None | Configuration dict |
| `get_max_resolution_configuration()` | Get max resolution configuration | None | Configuration dict |

### IMX500Device (Intelligent Vision Sensor)

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `load_ai_model(model_name, model_path=None)` | Load AI model | `model_name` (str): Model name<br>`model_path` (str, optional): Path to model file | `bool`: True if successful |
| `enable_ai_processing(enable=True)` | Enable/disable AI processing | `enable` (bool): Whether to enable processing | `bool`: True if successful |
| `process_frame(frame)` | Process frame with AI model | `frame`: Image frame to process | Dict with results |
| `get_device_id()` | Get device ID | None | Device ID string |

### HailoDevice (AI Accelerator)

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `load_model(model_path, config_path=None)` | Load AI model | `model_path` (str): Path to model file<br>`config_path` (str, optional): Path to configuration | `bool`: True if successful |
| `enable_processing(enable=True)` | Enable/disable processing | `enable` (bool): Whether to enable processing | `bool`: True if successful |
| `process_frame(frame)` | Process frame with loaded model | `frame`: Image frame to process | Dict with results |
| `get_device_info()` | Get device information | None | Dict with device info |
