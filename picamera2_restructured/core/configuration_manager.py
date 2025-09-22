"""
ConfigurationManager - Camera configuration management

This module provides functionality to manage camera configurations, including
creating, validating, and applying configurations for different camera use cases.

It abstracts the complexity of the Picamera2 configuration system and provides
simple, pre-defined configurations for common use cases.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

# Setup logging
logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Manages camera configurations
    
    This class provides methods for creating and managing camera configurations,
    including predefined configurations for common use cases.
    """
    
    def __init__(self, picam2):
        """
        Initialize configuration manager
        
        Args:
            picam2: Initialized Picamera2 instance
        """
        self._picam2 = picam2
        self._current_config = None
        
        # Predefined configuration templates
        self._config_templates = {
            'still': self._create_still_config,
            'video': self._create_video_config,
            'preview': self._create_preview_config,
            'high_resolution': self._create_high_res_config,
            'low_light': self._create_low_light_config,
        }
    
    def create_configuration(self, config_type: str = 'still', **kwargs) -> Dict[str, Any]:
        """
        Create a camera configuration
        
        Args:
            config_type: Type of configuration ('still', 'video', 'preview', etc.)
            **kwargs: Additional configuration parameters
            
        Returns:
            Dict containing camera configuration
        """
        try:
            # Use predefined template if available
            if config_type in self._config_templates:
                return self._config_templates[config_type](**kwargs)
            else:
                # Create default configuration
                logger.warning(f"Unknown config type '{config_type}', using default")
                return self._create_default_config(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create configuration: {e}")
            return self._create_default_config()
    
    def apply_configuration(self, config: Dict[str, Any] = None, config_type: str = None, **kwargs) -> bool:
        """
        Apply configuration to camera
        
        Args:
            config: Configuration dict to apply
            config_type: Type of configuration to create and apply
            **kwargs: Additional configuration parameters
            
        Returns:
            bool: True if configuration applied successfully
        """
        try:
            if config is None and config_type is not None:
                # Create configuration from template
                config = self.create_configuration(config_type, **kwargs)
            
            if config is None:
                # Use default configuration
                self._picam2.configure()
            else:
                # Apply provided configuration
                self._picam2.configure(config)
            
            self._current_config = config
            return True
        except Exception as e:
            logger.error(f"Failed to apply configuration: {e}")
            return False
    
    def _create_default_config(self, **kwargs) -> Dict[str, Any]:
        """Create default configuration"""
        try:
            config = self._picam2.create_still_configuration(**kwargs)
            return config
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
            return {}
    
    def _create_still_config(self, width: int = None, height: int = None, **kwargs) -> Dict[str, Any]:
        """Create configuration optimized for still image capture"""
        try:
            config_args = kwargs.copy()
            
            # Add resolution if provided
            if width is not None and height is not None:
                config_args['main'] = {"size": (width, height)}
                
                # Set lores stream for preview if not specified
                if "lores" not in config_args:
                    # Calculate lores resolution (1/4 of main)
                    lores_width = max(width // 4, 320)
                    lores_height = max(height // 4, 240)
                    config_args["lores"] = {"size": (lores_width, lores_height)}
                    
            # Create configuration
            config = self._picam2.create_still_configuration(**config_args)
            return config
        except Exception as e:
            logger.error(f"Failed to create still config: {e}")
            return self._create_default_config()
    
    def _create_video_config(self, width: int = 1920, height: int = 1080, fps: int = 30, **kwargs) -> Dict[str, Any]:
        """Create configuration optimized for video recording"""
        try:
            config_args = kwargs.copy()
            
            # Set video resolution
            config_args['main'] = {"size": (width, height)}
            
            # Set lores stream for preview if not specified
            if "lores" not in config_args:
                # Calculate lores resolution (1/4 of main)
                lores_width = max(width // 4, 320)
                lores_height = max(height // 4, 240)
                config_args["lores"] = {"size": (lores_width, lores_height)}
            
            # Set framerate
            if fps > 0:
                if "controls" not in config_args:
                    config_args["controls"] = {}
                
                config_args["controls"]["FrameRate"] = fps
            
            # Create configuration
            config = self._picam2.create_video_configuration(**config_args)
            return config
        except Exception as e:
            logger.error(f"Failed to create video config: {e}")
            return self._create_default_config()
    
    def _create_preview_config(self, width: int = 640, height: int = 480, **kwargs) -> Dict[str, Any]:
        """Create configuration optimized for preview"""
        try:
            config_args = kwargs.copy()
            
            # Set preview resolution
            config_args['main'] = {"size": (width, height)}
            
            # Create configuration
            config = self._picam2.create_preview_configuration(**config_args)
            return config
        except Exception as e:
            logger.error(f"Failed to create preview config: {e}")
            return self._create_default_config()
    
    def _create_high_res_config(self, **kwargs) -> Dict[str, Any]:
        """Create configuration for highest resolution still capture"""
        try:
            # Get maximum sensor resolution
            sensor_modes = self._picam2.sensor_modes
            if sensor_modes:
                max_width = 0
                max_height = 0
                max_mode = None
                
                # Find mode with highest resolution
                for mode in sensor_modes:
                    width = mode.get('size', (0, 0))[0]
                    height = mode.get('size', (0, 0))[1]
                    
                    if width * height > max_width * max_height:
                        max_width = width
                        max_height = height
                        max_mode = mode
                
                if max_mode:
                    return self._create_still_config(width=max_width, height=max_height, **kwargs)
            
            # Fallback to default high resolution
            return self._create_still_config(width=4056, height=3040, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create high-res config: {e}")
            return self._create_default_config()
    
    def _create_low_light_config(self, **kwargs) -> Dict[str, Any]:
        """Create configuration optimized for low light conditions"""
        try:
            config = self._create_still_config(**kwargs)
            
            # Add low-light specific controls
            controls = config.get('controls', {})
            controls.update({
                'AnalogueGain': 8.0,           # Increase gain
                'ExposureTime': 66666,         # Longer exposure (1/15s)
                'AwbEnable': 1,                # Enable auto white balance
                'NoiseReductionMode': 'HighQuality',  # High quality noise reduction
            })
            
            config['controls'] = controls
            return config
        except Exception as e:
            logger.error(f"Failed to create low-light config: {e}")
            return self._create_default_config()
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Get current camera configuration
        
        Returns:
            Dict containing current configuration
        """
        if self._current_config:
            return self._current_config
        
        try:
            return self._picam2.camera_config
        except Exception as e:
            logger.error(f"Failed to get current config: {e}")
            return {}
    
    def get_available_configs(self) -> List[str]:
        """
        Get list of available configuration templates
        
        Returns:
            List of configuration template names
        """
        return list(self._config_templates.keys())
