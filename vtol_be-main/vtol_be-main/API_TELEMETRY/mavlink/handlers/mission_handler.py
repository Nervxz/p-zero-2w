"""
Mission Handler for MAVLink API
Handles MAVLink mission protocol (download/upload/clear/current)
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink

logger = logging.getLogger(__name__)

@dataclass
class MissionItem:
    """Mission item data structure"""
    seq: int
    frame: int
    command: int
    current: int
    autocontinue: int
    param1: float
    param2: float
    param3: float
    param4: float
    x: float  # lat/x
    y: float  # lon/y
    z: float  # alt/z
    mission_type: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'seq': self.seq,
            'frame': self.frame,
            'command': self.command,
            'current': self.current,
            'autocontinue': self.autocontinue,
            'param1': self.param1,
            'param2': self.param2,
            'param3': self.param3,
            'param4': self.param4,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'mission_type': self.mission_type
        }

class MissionHandler:
    """Handler for MAVLink mission protocol operations"""
    
    def __init__(self, connection: mavutil.mavlink_connection):
        self.connection = connection
        self._mission_upload_items: List[MissionItem] = []
        self._mission_upload_index = 0
        self._mission_upload_in_progress = False
    
    def request_mission_list(self, mission_type: int = 0) -> bool:
        """
        Request mission count from vehicle
        
        Args:
            mission_type: Mission type (0=waypoints, 1=fence, 2=rally)
            
        Returns:
            bool: True if sent successfully
        """
        try:
            self.connection.mav.mission_request_list_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                mission_type=mission_type
            )
            logger.debug(f"Requested mission list (type {mission_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to request mission list: {e}")
            return False
    
    def request_mission_item(self, seq: int, mission_type: int = 0) -> bool:
        """
        Request specific mission item
        
        Args:
            seq: Mission item sequence number
            mission_type: Mission type (0=waypoints, 1=fence, 2=rally)
            
        Returns:
            bool: True if sent successfully
        """
        try:
            self.connection.mav.mission_request_int_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                seq=seq,
                mission_type=mission_type
            )
            logger.debug(f"Requested mission item {seq}")
            return True
        except Exception as e:
            logger.error(f"Failed to request mission item {seq}: {e}")
            return False
    
    def start_mission_upload(self, items: List[MissionItem], mission_type: int = 0) -> bool:
        """
        Start mission upload process
        
        Args:
            items: List of mission items to upload
            mission_type: Mission type (0=waypoints, 1=fence, 2=rally)
            
        Returns:
            bool: True if started successfully
        """
        try:
            if self._mission_upload_in_progress:
                logger.warning("Mission upload already in progress")
                return False
            
            self._mission_upload_items = items
            self._mission_upload_index = 0
            self._mission_upload_in_progress = True
            
            # Send mission count
            self.connection.mav.mission_count_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                count=len(items),
                mission_type=mission_type
            )
            
            logger.debug(f"Started mission upload with {len(items)} items")
            return True
        except Exception as e:
            logger.error(f"Failed to start mission upload: {e}")
            self._mission_upload_in_progress = False
            return False
    
    def handle_mission_request(self, seq: int, mission_type: int = 0) -> bool:
        """
        Handle mission request from autopilot during upload
        
        Args:
            seq: Requested sequence number
            mission_type: Mission type
            
        Returns:
            bool: True if handled successfully
        """
        try:
            if not self._mission_upload_in_progress:
                logger.warning("Received mission request but no upload in progress")
                return False
            
            if seq >= len(self._mission_upload_items):
                logger.error(f"Requested sequence {seq} out of range")
                return False
            
            item = self._mission_upload_items[seq]
            
            # Send mission item (INT format preferred)
            self.connection.mav.mission_item_int_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                seq=item.seq,
                frame=item.frame,
                command=item.command,
                current=item.current,
                autocontinue=item.autocontinue,
                param1=item.param1,
                param2=item.param2,
                param3=item.param3,
                param4=item.param4,
                x=int(item.x * 1e7) if item.frame in [0, 3] else int(item.x),  # lat/x
                y=int(item.y * 1e7) if item.frame in [0, 3] else int(item.y),  # lon/y
                z=item.z,
                mission_type=mission_type
            )
            
            logger.debug(f"Sent mission item {seq}")
            return True
        except Exception as e:
            logger.error(f"Failed to handle mission request for item {seq}: {e}")
            return False
    
    def handle_mission_request_legacy(self, seq: int, mission_type: int = 0) -> bool:
        """
        Handle legacy mission request (non-INT format)
        
        Args:
            seq: Requested sequence number
            mission_type: Mission type
            
        Returns:
            bool: True if handled successfully
        """
        try:
            if not self._mission_upload_in_progress:
                return False
            
            if seq >= len(self._mission_upload_items):
                return False
            
            item = self._mission_upload_items[seq]
            
            # Send legacy mission item (float format)
            self.connection.mav.mission_item_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                seq=item.seq,
                frame=item.frame,
                command=item.command,
                current=item.current,
                autocontinue=item.autocontinue,
                param1=item.param1,
                param2=item.param2,
                param3=item.param3,
                param4=item.param4,
                x=item.x,  # lat/x as float
                y=item.y,  # lon/y as float
                z=item.z,
                mission_type=mission_type
            )
            
            logger.debug(f"Sent legacy mission item {seq}")
            return True
        except Exception as e:
            logger.error(f"Failed to handle legacy mission request for item {seq}: {e}")
            return False
    
    def complete_mission_upload(self):
        """Complete mission upload process"""
        self._mission_upload_in_progress = False
        self._mission_upload_items.clear()
        self._mission_upload_index = 0
        logger.debug("Mission upload completed")
    
    def clear_mission(self, mission_type: int = 0) -> bool:
        """
        Clear all missions on vehicle
        
        Args:
            mission_type: Mission type (0=waypoints, 1=fence, 2=rally)
            
        Returns:
            bool: True if sent successfully
        """
        try:
            self.connection.mav.mission_clear_all_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                mission_type=mission_type
            )
            logger.debug(f"Cleared mission (type {mission_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to clear mission: {e}")
            return False
    
    def set_current_mission_item(self, seq: int) -> bool:
        """
        Set current mission item
        
        Args:
            seq: Mission item sequence number to set as current
            
        Returns:
            bool: True if sent successfully
        """
        try:
            self.connection.mav.mission_set_current_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                seq=seq
            )
            logger.debug(f"Set current mission item to {seq}")
            return True
        except Exception as e:
            logger.error(f"Failed to set current mission item: {e}")
            return False
    
    def request_home_position(self) -> bool:
        """
        Request home position from vehicle
        
        Returns:
            bool: True if sent successfully
        """
        try:
            # Request HOME_POSITION message
            self.connection.mav.command_long_send(
                target_system=self.connection.target_system,
                target_component=self.connection.target_component,
                command=mavlink.MAV_CMD_GET_HOME_POSITION,
                confirmation=0,
                param1=0, param2=0, param3=0, param4=0,
                param5=0, param6=0, param7=0
            )
            logger.debug("Requested home position")
            return True
        except Exception as e:
            logger.error(f"Failed to request home position: {e}")
            return False
    
    def create_waypoint_item(self, seq: int, lat: float, lon: float, alt: float,
                           hold_time: float = 0.0, accept_radius: float = 0.0,
                           pass_radius: float = 0.0, yaw: float = float('nan')) -> MissionItem:
        """
        Create a waypoint mission item
        
        Args:
            seq: Sequence number
            lat: Latitude (degrees)
            lon: Longitude (degrees)
            alt: Altitude (meters)
            hold_time: Hold time at waypoint (seconds)
            accept_radius: Acceptance radius (meters)
            pass_radius: Pass-through radius (meters)
            yaw: Target yaw angle (degrees)
            
        Returns:
            MissionItem: Created mission item
        """
        return MissionItem(
            seq=seq,
            frame=mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            command=mavlink.MAV_CMD_NAV_WAYPOINT,
            current=1 if seq == 0 else 0,
            autocontinue=1,
            param1=hold_time,
            param2=accept_radius,
            param3=pass_radius,
            param4=yaw,
            x=lat,
            y=lon,
            z=alt
        )
    
    def create_takeoff_item(self, seq: int, alt: float, pitch: float = 0.0,
                          yaw: float = float('nan'), lat: float = 0.0, 
                          lon: float = 0.0) -> MissionItem:
        """
        Create a takeoff mission item
        
        Args:
            seq: Sequence number
            alt: Target altitude (meters)
            pitch: Minimum pitch angle (degrees)
            yaw: Target yaw angle (degrees)
            lat: Takeoff latitude (0 = current position)
            lon: Takeoff longitude (0 = current position)
            
        Returns:
            MissionItem: Created mission item
        """
        return MissionItem(
            seq=seq,
            frame=mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            command=mavlink.MAV_CMD_NAV_TAKEOFF,
            current=1 if seq == 0 else 0,
            autocontinue=1,
            param1=pitch,
            param2=0,
            param3=0,
            param4=yaw,
            x=lat,
            y=lon,
            z=alt
        )
    
    def create_land_item(self, seq: int, lat: float = 0.0, lon: float = 0.0,
                        abort_alt: float = 0.0, precision_land: int = 0,
                        yaw: float = float('nan')) -> MissionItem:
        """
        Create a land mission item
        
        Args:
            seq: Sequence number
            lat: Landing latitude (0 = current position)
            lon: Landing longitude (0 = current position)
            abort_alt: Abort altitude (meters)
            precision_land: Precision landing mode
            yaw: Landing yaw angle (degrees)
            
        Returns:
            MissionItem: Created mission item
        """
        return MissionItem(
            seq=seq,
            frame=mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            command=mavlink.MAV_CMD_NAV_LAND,
            current=0,
            autocontinue=1,
            param1=abort_alt,
            param2=precision_land,
            param3=0,
            param4=yaw,
            x=lat,
            y=lon,
            z=0
        )
