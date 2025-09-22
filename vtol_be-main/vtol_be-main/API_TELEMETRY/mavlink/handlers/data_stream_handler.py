"""
Data Stream Handler for MAVLink API
Handles MAVLink data stream requests and configuration
"""

import logging
from typing import Optional
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink

logger = logging.getLogger(__name__)

class DataStreamHandler:
    """Handler for MAVLink data stream requests"""
    
    def __init__(self, connection: mavutil.mavlink_connection):
        self.connection = connection
    
    def request_data_stream(self, stream_id: int, rate_hz: int, start_stop: bool = True) -> bool:
        """
        Request specific MAVLink data stream
        
        Args:
            stream_id: MAV_DATA_STREAM_* constant
            rate_hz: Request rate in Hz
            start_stop: True to start, False to stop
            
        Returns:
            bool: True if sent successfully
        """
        try:
            self.connection.mav.request_data_stream_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                req_stream_id=stream_id,
                req_message_rate=rate_hz,
                start_stop=1 if start_stop else 0
            )
            logger.debug(f"Requested data stream {stream_id} at {rate_hz}Hz")
            return True
        except Exception as e:
            logger.error(f"Failed to request data stream {stream_id}: {e}")
            return False
    
    def request_all_data_streams(self, rate_hz: int = 4) -> bool:
        """Request all MAVLink data streams"""
        return self.request_data_stream(mavlink.MAV_DATA_STREAM_ALL, rate_hz)
    
    def request_attitude_stream(self, rate_hz: int = 10) -> bool:
        """Request attitude data stream (MAV_DATA_STREAM_EXTRA1)"""
        return self.request_data_stream(mavlink.MAV_DATA_STREAM_EXTRA1, rate_hz)
    
    def request_position_stream(self, rate_hz: int = 3) -> bool:
        """Request position data stream (MAV_DATA_STREAM_POSITION)"""
        return self.request_data_stream(mavlink.MAV_DATA_STREAM_POSITION, rate_hz)
    
    def request_vfr_hud_stream(self, rate_hz: int = 5) -> bool:
        """Request VFR HUD data stream (MAV_DATA_STREAM_EXTRA2)"""
        return self.request_data_stream(mavlink.MAV_DATA_STREAM_EXTRA2, rate_hz)
    
    def request_extended_status_stream(self, rate_hz: int = 2) -> bool:
        """Request extended status data stream"""
        return self.request_data_stream(mavlink.MAV_DATA_STREAM_EXTENDED_STATUS, rate_hz)
    
    def configure_standard_streams(self) -> bool:
        """Configure standard MAVLink data streams with typical rates"""
        streams = [
            (mavlink.MAV_DATA_STREAM_EXTRA1, 10),      # Attitude
            (mavlink.MAV_DATA_STREAM_POSITION, 3),     # Position
            (mavlink.MAV_DATA_STREAM_EXTRA2, 5),       # VFR HUD
            (mavlink.MAV_DATA_STREAM_EXTENDED_STATUS, 2), # Extended status
            (mavlink.MAV_DATA_STREAM_RAW_SENSORS, 2),  # Raw sensors
            (mavlink.MAV_DATA_STREAM_RC_CHANNELS, 5),  # RC channels
        ]
        
        success = True
        for stream_id, rate in streams:
            if not self.request_data_stream(stream_id, rate):
                success = False
        
        return success
    
    def stop_all_data_streams(self) -> bool:
        """Stop all MAVLink data streams"""
        return self.request_data_stream(mavlink.MAV_DATA_STREAM_ALL, 0, False)
    
    def set_stream_rate(self, message_name: str, rate_hz: int) -> bool:
        """
        Set stream rate for specific message using SET_MESSAGE_INTERVAL
        
        Args:
            message_name: MAVLink message name (e.g., 'ATTITUDE', 'GLOBAL_POSITION_INT')
            rate_hz: Rate in Hz (0 to stop)
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Get message ID from name
            msg_id = getattr(mavlink, f'MAVLINK_MSG_ID_{message_name}', None)
            if msg_id is None:
                logger.error(f"Unknown message: {message_name}")
                return False
            
            # Calculate interval in microseconds
            interval_us = int(1000000 / rate_hz) if rate_hz > 0 else -1
            
            self.connection.mav.command_long_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                command=mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
                confirmation=0,
                param1=msg_id,
                param2=interval_us,
                param3=0,
                param4=0,
                param5=0,
                param6=0,
                param7=0
            )
            
            logger.debug(f"Set {message_name} rate to {rate_hz}Hz")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set stream rate for {message_name}: {e}")
            return False
