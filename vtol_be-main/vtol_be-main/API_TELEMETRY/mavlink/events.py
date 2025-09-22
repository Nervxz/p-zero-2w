"""
MAVLink Event System for Python DroneMAVLinkAPI
Defines event types, event data structure and event handling system
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

class MAVLinkEventType(Enum):
    """Event types for MAVLink messages and system events"""
    HEARTBEAT = auto()                  # Heartbeat từ drone
    ATTITUDE = auto()                   # Dữ liệu góc nghiêng (roll, pitch, yaw)
    POSITION = auto()                   # Vị trí GPS và altitude
    STATUS_TEXT = auto()                # Tin nhắn trạng thái từ drone
    BATTERY_STATUS = auto()             # Thông tin pin
    GPS_INFO = auto()                   # Thông tin GPS chi tiết
    VFR_HUD = auto()                    # Dữ liệu VFR HUD (tốc độ, độ cao)
    PARAMETER_RECEIVED = auto()         # Tham số nhận được
    ALL_PARAMETERS_RECEIVED = auto()    # Tất cả tham số đã nhận
    SYS_STATUS = auto()                 # SysStatus (raw)
    COMMAND_ACK = auto()                # Command ACK (raw)
    CONNECTION_STATE_CHANGED = auto()   # Thay đổi trạng thái kết nối
    
    # Mission Protocol Events
    MISSION_COUNT = auto()              # Mission count received
    MISSION_ITEM = auto()               # Mission item received
    MISSION_DOWNLOAD_PROGRESS = auto()  # Mission download progress
    MISSION_DOWNLOAD_COMPLETE = auto()  # Mission download complete
    MISSION_UPLOAD_PROGRESS = auto()    # Mission upload progress
    MISSION_UPLOAD_COMPLETE = auto()    # Mission upload complete
    MISSION_CURRENT = auto()            # Current mission item
    MISSION_ITEM_REACHED = auto()       # Mission item reached
    MISSION_ACK = auto()                # Mission acknowledgment
    MISSION_CLEARED = auto()            # Mission cleared
    HOME_POSITION = auto()              # Home position received

@dataclass
class MAVLinkEvent:
    """MAVLink event data structure"""
    event_type: MAVLinkEventType
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def type(self) -> MAVLinkEventType:
        """Compatibility property for event_type"""
        return self.event_type
