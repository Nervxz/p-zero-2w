"""
DeviceManager - Management of camera devices and hardware accelerators

This module provides functionality to detect, initialize, and manage
different camera devices and hardware accelerators.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import os
import importlib

from .base_device import BaseDevice

# Setup logging
logger = logging.getLogger(__name__)


class DeviceManager:
    """
    Manages camera devices and hardware accelerators
    
    This class provides functionality to detect, initialize, and manage
    different camera devices and hardware accelerators.
    """
    
    def __init__(self):
        """Initialize device manager"""
        self._devices = {}
        self._detected_devices = {}
        
        # Register builtin device types
        self._device_types = {
            'imx708': self._create_imx708,
            'imx500': self._create_imx500,
            'hailo': self._create_hailo,
        }
        
        logger.debug("DeviceManager initialized")
    
    def detect_devices(self) -> Dict[str, str]:
        """
        Detect available camera devices
        
        Returns:
            Dict mapping device names to device types
        """
        detected = {}
        
        try:
            # Import original Picamera2 for detection
            from picamera2.picamera2 import Picamera2
            
            # Check available cameras
            camera_manager = Picamera2._cm
            num_cameras = camera_manager.get_num_cameras()
            
            for i in range(num_cameras):
                try:
                    # Get camera information
                    info = camera_manager.get_camera_info(i)
                    if not info:
                        continue
                        
                    model = info.get('Model', '').lower()
                    location = info.get('Location', '').lower()
                    
                    # Determine device type
                    device_type = 'generic'
                    if 'imx708' in model:
                        device_type = 'imx708'
                    elif 'imx500' in model:
                        device_type = 'imx500'
                    
                    # Add to detected devices
                    device_name = f"camera{i}"
                    detected[device_name] = device_type
                    
                    logger.info(f"Detected camera: {device_name} ({device_type}) - {model} at {location}")
                    
                except Exception as e:
                    logger.error(f"Error detecting camera {i}: {e}")
            
            # Check for hardware accelerators
            self._detect_hardware_accelerators(detected)
            
        except Exception as e:
            logger.error(f"Error in device detection: {e}")
        
        self._detected_devices = detected
        return detected
    
    def _detect_hardware_accelerators(self, detected: Dict[str, str]):
        """Detect hardware accelerators"""
        # Check for Hailo AI accelerator
        try:
            import hailopython
            detected['hailo'] = 'hailo'
            logger.info("Detected Hailo AI accelerator")
        except ImportError:
            pass
    
    def initialize_device(self, device_name: str, device_type: str = None) -> Optional[BaseDevice]:
        """
        Initialize a device
        
        Args:
            device_name: Device name
            device_type: Device type (if None, use detected type)
            
        Returns:
            Initialized device or None if initialization failed
        """
        # Use detected type if not specified
        if device_type is None:
            if not self._detected_devices:
                self.detect_devices()
            
            device_type = self._detected_devices.get(device_name, 'generic')
        
        # Check if device is already initialized
        if device_name in self._devices:
            return self._devices[device_name]
        
        try:
            # Create device based on type
            device_creator = self._device_types.get(device_type)
            
            if device_creator:
                device = device_creator(device_name)
                if device and device.initialize():
                    self._devices[device_name] = device
                    return device
                else:
                    logger.error(f"Failed to initialize {device_type} device '{device_name}'")
                    return None
            else:
                logger.error(f"Unsupported device type: {device_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error initializing device '{device_name}': {e}")
            return None
    
    def _create_imx708(self, device_name: str) -> BaseDevice:
        """Create IMX708 device"""
        try:
            from .imx708_device import IMX708Device
            return IMX708Device(device_name)
        except ImportError:
            logger.error(f"Failed to import IMX708Device")
            return None
    
    def _create_imx500(self, device_name: str) -> BaseDevice:
        """Create IMX500 device"""
        try:
            from .imx500_device import IMX500Device
            return IMX500Device(device_name)
        except ImportError:
            logger.error(f"Failed to import IMX500Device")
            return None
    
    def _create_hailo(self, device_name: str) -> BaseDevice:
        """Create Hailo device"""
        try:
            from .hailo_device import HailoDevice
            return HailoDevice(device_name)
        except ImportError:
            logger.error(f"Failed to import HailoDevice")
            return None
    
    def get_device(self, device_name: str) -> Optional[BaseDevice]:
        """
        Get initialized device
        
        Args:
            device_name: Device name
            
        Returns:
            Device or None if not initialized
        """
        return self._devices.get(device_name)
    
    def release_device(self, device_name: str) -> bool:
        """
        Release device resources
        
        Args:
            device_name: Device name
            
        Returns:
            bool: True if device released successfully
        """
        device = self._devices.get(device_name)
        if device:
            try:
                if device.release():
                    del self._devices[device_name]
                    return True
                return False
            except Exception as e:
                logger.error(f"Error releasing device '{device_name}': {e}")
                return False
        return True
    
    def release_all_devices(self):
        """Release all device resources"""
        for device_name in list(self._devices.keys()):
            self.release_device(device_name)
    
    def get_available_device_types(self) -> List[str]:
        """
        Get list of available device types
        
        Returns:
            List of device type names
        """
        return list(self._device_types.keys())
