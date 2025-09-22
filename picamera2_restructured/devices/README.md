# PiCamera2 Devices Module

This module provides device-specific implementations for different camera modules and AI acceleration hardware.

## Overview

The devices module contains specialized code for specific camera sensors and accelerator hardware, enabling optimized configurations and feature access tailored to each device's capabilities.

## Supported Devices

### IMX708

The Sony IMX708 is the 12MP camera sensor used in the Raspberry Pi Camera Module 3:

- 12 megapixel resolution (4608 × 2592)
- Autofocus capability
- HDR support
- Wide dynamic range

```python
# Device-specific features are accessed through the API
camera = CameraController()
camera.initialize()

# The appropriate device driver is automatically selected
# based on the detected camera hardware
```

### IMX500

The Sony IMX500 intelligent vision sensor with embedded AI processing:

- AI acceleration for on-device machine learning
- Object detection
- Classification
- Pose estimation

```python
# For IMX500-specific AI features
from picamera2_restructured.devices.imx500 import IMX500Device

# Can be used through the device manager
device_manager = DeviceManager()
imx500 = device_manager.initialize_device("camera0", "imx500")
if imx500:
    imx500.load_ai_model("efficientdet")
    imx500.enable_ai_processing()
```

### Hailo

Support for Hailo AI accelerators for enhanced AI processing with PiCamera2:

- Hardware acceleration for neural networks
- Efficient inference for computer vision tasks
- Low power consumption

```python
# For Hailo-specific acceleration
from picamera2_restructured.devices.hailo import HailoDevice
```

## Device Management

The DeviceManager class provides functionality to detect, initialize, and manage different camera devices and hardware accelerators:

```python
from picamera2_restructured.devices import DeviceManager

# Create device manager
manager = DeviceManager()

# Detect available devices
devices = manager.detect_devices()
print(f"Detected devices: {devices}")

# Initialize a specific device
device = manager.initialize_device("camera0")
if device:
    config = device.get_recommended_configuration()
    # Use device-specific configuration
```
