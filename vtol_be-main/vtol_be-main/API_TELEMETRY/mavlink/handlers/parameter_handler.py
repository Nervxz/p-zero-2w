"""
Parameter Handler for MAVLink API
Handles MAVLink parameter read/write operations
"""

import logging
from typing import Optional, Dict, Any
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink

logger = logging.getLogger(__name__)

class ParameterHandler:
    """Handler for MAVLink parameter operations"""
    
    def __init__(self, connection: mavutil.mavlink_connection):
        self.connection = connection
    
    def request_parameter_list(self) -> bool:
        """Request all parameters from vehicle"""
        try:
            self.connection.mav.param_request_list_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component
            )
            logger.debug("Requested parameter list")
            return True
        except Exception as e:
            logger.error(f"Failed to request parameter list: {e}")
            return False
    
    def request_parameter(self, param_name: str, param_index: int = -1) -> bool:
        """
        Request specific parameter
        
        Args:
            param_name: Parameter name (up to 16 chars)
            param_index: Parameter index (-1 to use name)
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Ensure param_name is properly encoded and padded
            param_id = param_name.encode('utf-8')[:16]
            param_id = param_id.ljust(16, b'\0')
            
            self.connection.mav.param_request_read_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                param_id=param_id,
                param_index=param_index
            )
            logger.debug(f"Requested parameter: {param_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to request parameter {param_name}: {e}")
            return False
    
    def set_parameter(self, param_name: str, param_value: float, param_type: int = mavlink.MAV_PARAM_TYPE_REAL32) -> bool:
        """
        Set parameter value
        
        Args:
            param_name: Parameter name (up to 16 chars)
            param_value: Parameter value
            param_type: Parameter type (MAV_PARAM_TYPE_*)
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Ensure param_name is properly encoded and padded
            param_id = param_name.encode('utf-8')[:16]
            param_id = param_id.ljust(16, b'\0')
            
            self.connection.mav.param_set_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                param_id=param_id,
                param_value=param_value,
                param_type=param_type
            )
            logger.debug(f"Set parameter {param_name} = {param_value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set parameter {param_name}: {e}")
            return False
    
    def get_parameter_type_from_value(self, value: Any) -> int:
        """Get appropriate MAVLink parameter type from Python value"""
        if isinstance(value, bool):
            return mavlink.MAV_PARAM_TYPE_UINT8
        elif isinstance(value, int):
            if -128 <= value <= 127:
                return mavlink.MAV_PARAM_TYPE_INT8
            elif 0 <= value <= 255:
                return mavlink.MAV_PARAM_TYPE_UINT8
            elif -32768 <= value <= 32767:
                return mavlink.MAV_PARAM_TYPE_INT16
            elif 0 <= value <= 65535:
                return mavlink.MAV_PARAM_TYPE_UINT16
            elif -2147483648 <= value <= 2147483647:
                return mavlink.MAV_PARAM_TYPE_INT32
            else:
                return mavlink.MAV_PARAM_TYPE_UINT32
        elif isinstance(value, float):
            return mavlink.MAV_PARAM_TYPE_REAL32
        else:
            return mavlink.MAV_PARAM_TYPE_REAL32
