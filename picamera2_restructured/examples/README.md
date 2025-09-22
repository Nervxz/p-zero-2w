# PiCamera2 Restructured Examples

This directory contains example scripts that demonstrate how to use the restructured PiCamera2 library.

## Basic Examples

- **basic_capture.py**: Simple image capture example
- **preview_and_capture.py**: Start a preview window and capture when the user presses a key
- **video_recording.py**: Record video with a preview window
- **timelapse.py**: Capture a sequence of images at regular intervals

## Advanced Examples

- **advanced_capture.py**: Demonstrates advanced capture features (raw, burst, image processing)

## Running the Examples

1. Make sure you have a Raspberry Pi with a camera module connected
2. Ensure the picamera2_restructured library is in your Python path
3. Run any example script:

```bash
python3 basic_capture.py
```

## Tips

- The examples are designed to work out-of-the-box with minimal configuration
- Each example demonstrates different aspects of the library's functionality
- Examples can be combined and modified to create custom applications
- All examples include proper resource cleanup (closing the camera) even if an error occurs
