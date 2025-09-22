"""
MAVLink Core Connection Management and Message Processing
Handles serial connection, message parsing, and event distribution
"""

import serial
import threading
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable, List, Set
from queue import Queue
import logging
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink

from .events import MAVLinkEvent, MAVLinkEventType
from .handlers.data_stream_handler import DataStreamHandler
from .handlers.parameter_handler import ParameterHandler
from .handlers.command_handler import CommandHandler
from .handlers.mission_handler import MissionHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MAVLinkConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"  # Chưa kết nối
    CONNECTED = "connected"        # Đã kết nối
    CONNECTING = "connecting"      # Đang kết nối
    ERROR = "error"               # Lỗi kết nối

class DroneMAVLinkAPI:
    """
    Main DroneMAVLink API class for Python
    Provides comprehensive MAVLink communication with modular event-driven architecture
    """
    
    def __init__(self):
        # Connection management
        self._connection: Optional[mavutil.mavlink_connection] = None
        self._connection_state = MAVLinkConnectionState.DISCONNECTED
        self._connection_port = ""
        self._connection_baud = 115200
        
        # Threading
        self._read_thread: Optional[threading.Thread] = None
        self._should_stop = False
        self._lock = threading.RLock()
        
        # Event system
        self._event_listeners: Dict[MAVLinkEventType, List[Callable]] = {}
        self._event_queue: Queue = Queue()
        
        # Vehicle state cache
        self._vehicle_data: Dict[str, Any] = {}
        self._parameters: Dict[str, float] = {}
        self._parameter_count = 0
        self._parameters_received = 0
        
        # Mission state
        self._mission_items: List[Dict[str, Any]] = []
        self._mission_count = 0
        self._current_mission_seq = 0
        
        # Handler instances (created after connection)
        self._data_stream_handler: Optional[DataStreamHandler] = None
        self._parameter_handler: Optional[ParameterHandler] = None
        self._command_handler: Optional[CommandHandler] = None
        self._mission_handler: Optional[MissionHandler] = None
        
        # Auto-reconnection
        self._auto_reconnect = True
        self._reconnect_delay = 5.0
        self._max_reconnect_attempts = 10
        self._reconnect_count = 0
        
        logger.info("DroneMAVLinkAPI initialized")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to vehicle"""
        return self._connection_state == MAVLinkConnectionState.CONNECTED
    
    @property
    def connection_state(self) -> MAVLinkConnectionState:
        """Get current connection state"""
        return self._connection_state
    
    @property
    def parameters(self) -> Dict[str, float]:
        """Get all received parameters"""
        with self._lock:
            return self._parameters.copy()
    
    def connect(self, port: str, baud_rate: int = 115200, timeout: float = 10.0) -> bool:
        """
        Connect to MAVLink vehicle
        
        Args:
            port: Serial port path (e.g., '/dev/ttyACM0', 'COM3')
            baud_rate: Serial baud rate
            timeout: Connection timeout in seconds
            
        Returns:
            bool: True if connected successfully
        """
        if self.is_connected:
            logger.warning("Already connected")
            return True
        
        self._connection_port = port
        self._connection_baud = baud_rate
        
        try:
            self._set_connection_state(MAVLinkConnectionState.CONNECTING)
            logger.info(f"Connecting to {port} at {baud_rate} baud...")
            
            # Create MAVLink connection
            self._connection = mavutil.mavlink_connection(
                port,
                baud=baud_rate,
                timeout=timeout,
                robust_parsing=True
            )
            
            # Wait for heartbeat
            logger.info("Waiting for heartbeat...")
            heartbeat = self._connection.wait_heartbeat(timeout=timeout)
            
            if heartbeat:
                logger.info(f"Heartbeat received from system {heartbeat.get_srcSystem()}")
                self._set_connection_state(MAVLinkConnectionState.CONNECTED)
                
                # Start read thread
                self._should_stop = False
                self._read_thread = threading.Thread(target=self._read_messages, daemon=True)
                self._read_thread.start()
                
                # Initialize handlers
                self._init_handlers()
                
                # Reset reconnect counter
                self._reconnect_count = 0
                
                # Configure initial data streams
                self.request_all_data_streams()
                
                return True
            else:
                logger.error("No heartbeat received")
                self._set_connection_state(MAVLinkConnectionState.ERROR)
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._set_connection_state(MAVLinkConnectionState.ERROR)
            return False
    
    def disconnect(self):
        """Disconnect from vehicle"""
        logger.info("Disconnecting...")
        
        self._should_stop = True
        self._auto_reconnect = False
        
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2.0)
        
        if self._connection:
            try:
                self._connection.close()
            except:
                pass
            self._connection = None
        
        self._set_connection_state(MAVLinkConnectionState.DISCONNECTED)
        logger.info("Disconnected")
    
    def _init_handlers(self):
        """Initialize handler instances after connection"""
        if self._connection:
            self._data_stream_handler = DataStreamHandler(self._connection)
            self._parameter_handler = ParameterHandler(self._connection)
            self._command_handler = CommandHandler(self._connection)
            self._mission_handler = MissionHandler(self._connection)
    
    def _set_connection_state(self, state: MAVLinkConnectionState):
        """Set connection state and emit event"""
        old_state = self._connection_state
        self._connection_state = state
        
        if old_state != state:
            self._emit_event(MAVLinkEventType.CONNECTION_STATE_CHANGED, state)
    
    def _read_messages(self):
        """Background thread to read MAVLink messages"""
        logger.info("Message reader thread started")
        
        while not self._should_stop:
            try:
                if not self._connection:
                    break
                
                msg = self._connection.recv_msg()
                if msg:
                    self._handle_message(msg)
                else:
                    time.sleep(0.001)  # Small delay to prevent CPU spinning
                    
            except Exception as e:
                logger.error(f"Message reading error: {e}")
                if self._auto_reconnect and not self._should_stop:
                    self._attempt_reconnection()
                break
        
        logger.info("Message reader thread stopped")
    
    def _handle_message(self, msg):
        """Handle incoming MAVLink message"""
        try:
            msg_type = msg.get_type()
            
            # Route message to appropriate handler
            if msg_type == 'HEARTBEAT':
                self._handle_heartbeat(msg)
            elif msg_type == 'ATTITUDE':
                self._handle_attitude(msg)
            elif msg_type == 'GLOBAL_POSITION_INT':
                self._handle_global_position(msg)
            elif msg_type == 'GPS_RAW_INT':
                self._handle_gps_raw(msg)
            elif msg_type == 'VFR_HUD':
                self._handle_vfr_hud(msg)
            elif msg_type == 'BATTERY_STATUS':
                self._handle_battery_status(msg)
            elif msg_type == 'SYS_STATUS':
                self._handle_sys_status(msg)
            elif msg_type == 'STATUSTEXT':
                self._handle_status_text(msg)
            elif msg_type == 'PARAM_VALUE':
                self._handle_param_value(msg)
            elif msg_type == 'COMMAND_ACK':
                self._handle_command_ack(msg)
            # Mission protocol messages
            elif msg_type == 'MISSION_COUNT':
                self._handle_mission_count(msg)
            elif msg_type == 'MISSION_ITEM_INT':
                self._handle_mission_item_int(msg)
            elif msg_type == 'MISSION_ITEM':
                self._handle_mission_item(msg)
            elif msg_type == 'MISSION_ACK':
                self._handle_mission_ack(msg)
            elif msg_type == 'MISSION_CURRENT':
                self._handle_mission_current(msg)
            elif msg_type == 'MISSION_ITEM_REACHED':
                self._handle_mission_item_reached(msg)
            elif msg_type == 'HOME_POSITION':
                self._handle_home_position(msg)
            # Mission upload protocol handling
            elif msg_type == 'MISSION_REQUEST_INT' and self._mission_handler:
                self._mission_handler.handle_mission_request(msg.seq, getattr(msg, 'mission_type', 0))
            elif msg_type == 'MISSION_REQUEST' and self._mission_handler:
                self._mission_handler.handle_mission_request_legacy(msg.seq, getattr(msg, 'mission_type', 0))
                
        except Exception as e:
            logger.error(f"Error handling {msg.get_type()}: {e}")
    
    def _handle_heartbeat(self, msg):
        """Handle HEARTBEAT message"""
        data = {
            'system_id': msg.get_srcSystem(),
            'component_id': msg.get_srcComponent(),
            'type': msg.type,
            'autopilot': msg.autopilot,
            'base_mode': msg.base_mode,
            'custom_mode': msg.custom_mode,
            'system_status': msg.system_status,
            'mavlink_version': msg.mavlink_version,
            'armed': bool(msg.base_mode & mavlink.MAV_MODE_FLAG_SAFETY_ARMED),
            'mode': self._get_flight_mode_name(msg.custom_mode)
        }
        
        with self._lock:
            self._vehicle_data.update(data)
        
        self._emit_event(MAVLinkEventType.HEARTBEAT, data)
    
    def _handle_attitude(self, msg):
        """Handle ATTITUDE message"""
        import math
        
        data = {
            'roll': math.degrees(msg.roll),
            'pitch': math.degrees(msg.pitch),
            'yaw': math.degrees(msg.yaw),
            'rollspeed': math.degrees(msg.rollspeed),
            'pitchspeed': math.degrees(msg.pitchspeed),
            'yawspeed': math.degrees(msg.yawspeed)
        }
        
        with self._lock:
            self._vehicle_data.update(data)
        
        self._emit_event(MAVLinkEventType.ATTITUDE, data)
    
    def _handle_global_position(self, msg):
        """Handle GLOBAL_POSITION_INT message"""
        data = {
            'lat': msg.lat / 1e7,
            'lon': msg.lon / 1e7,
            'alt': msg.alt / 1000.0,  # mm to m
            'relative_alt': msg.relative_alt / 1000.0,  # mm to m
            'vx': msg.vx / 100.0,  # cm/s to m/s
            'vy': msg.vy / 100.0,
            'vz': msg.vz / 100.0,
            'hdg': msg.hdg / 100.0  # cdeg to deg
        }
        
        with self._lock:
            self._vehicle_data.update(data)
        
        self._emit_event(MAVLinkEventType.POSITION, data)
    
    def _handle_gps_raw(self, msg):
        """Handle GPS_RAW_INT message"""
        data = {
            'fix_type': msg.fix_type,
            'satellites_visible': msg.satellites_visible,
            'lat': msg.lat / 1e7 if msg.lat != 0 else None,
            'lon': msg.lon / 1e7 if msg.lon != 0 else None,
            'alt': msg.alt / 1000.0 if msg.alt != 0 else None,
            'eph': msg.eph / 100.0 if msg.eph != 65535 else None,
            'epv': msg.epv / 100.0 if msg.epv != 65535 else None,
            'vel': msg.vel / 100.0 if msg.vel != 65535 else None,
            'cog': msg.cog / 100.0 if msg.cog != 65535 else None
        }
        
        with self._lock:
            self._vehicle_data.update({'gps': data})
        
        self._emit_event(MAVLinkEventType.GPS_INFO, data)
    
    def _handle_vfr_hud(self, msg):
        """Handle VFR_HUD message"""
        data = {
            'airspeed': msg.airspeed,
            'groundspeed': msg.groundspeed,
            'heading': msg.heading,
            'throttle': msg.throttle,
            'alt': msg.alt,
            'climb': msg.climb
        }
        
        with self._lock:
            self._vehicle_data.update(data)
        
        self._emit_event(MAVLinkEventType.VFR_HUD, data)
    
    def _handle_battery_status(self, msg):
        """Handle BATTERY_STATUS message"""
        data = {
            'id': msg.id,
            'battery_function': msg.battery_function,
            'type': msg.type,
            'temperature': msg.temperature / 100.0,  # cdegC to degC
            'voltages': [v / 1000.0 for v in msg.voltages if v != 65535],  # mV to V
            'current_battery': msg.current_battery / 100.0,  # cA to A
            'current_consumed': msg.current_consumed,  # mAh
            'energy_consumed': msg.energy_consumed,  # hJ
            'battery_remaining': msg.battery_remaining,  # %
            'time_remaining': msg.time_remaining,  # seconds
            'charge_state': msg.charge_state
        }
        
        with self._lock:
            self._vehicle_data.update({'battery': data})
        
        self._emit_event(MAVLinkEventType.BATTERY_STATUS, data)
    
    def _handle_sys_status(self, msg):
        """Handle SYS_STATUS message"""
        data = {
            'onboard_control_sensors_present': msg.onboard_control_sensors_present,
            'onboard_control_sensors_enabled': msg.onboard_control_sensors_enabled,
            'onboard_control_sensors_health': msg.onboard_control_sensors_health,
            'load': msg.load / 10.0,  # d% to %
            'voltage_battery': msg.voltage_battery / 1000.0,  # mV to V
            'current_battery': msg.current_battery / 100.0,  # cA to A
            'battery_remaining': msg.battery_remaining,  # %
            'drop_rate_comm': msg.drop_rate_comm / 100.0,  # c% to %
            'errors_comm': msg.errors_comm,
            'errors_count1': msg.errors_count1,
            'errors_count2': msg.errors_count2,
            'errors_count3': msg.errors_count3,
            'errors_count4': msg.errors_count4
        }
        
        with self._lock:
            self._vehicle_data.update({'sys_status': data})
        
        self._emit_event(MAVLinkEventType.SYS_STATUS, data)
    
    def _handle_status_text(self, msg):
        """Handle STATUSTEXT message"""
        data = {
            'severity': msg.severity,
            'text': msg.text.decode('utf-8').rstrip('\0'),
            'id': getattr(msg, 'id', 0),
            'chunk_seq': getattr(msg, 'chunk_seq', 0)
        }
        
        self._emit_event(MAVLinkEventType.STATUS_TEXT, data)
    
    def _handle_param_value(self, msg):
        """Handle PARAM_VALUE message"""
        param_id = msg.param_id.decode('utf-8').rstrip('\0')
        param_value = msg.param_value
        
        with self._lock:
            self._parameters[param_id] = param_value
            self._parameter_count = msg.param_count
            self._parameters_received = msg.param_index + 1
        
        data = {
            'id': param_id,
            'value': param_value,
            'type': msg.param_type,
            'index': msg.param_index,
            'count': msg.param_count
        }
        
        self._emit_event(MAVLinkEventType.PARAMETER_RECEIVED, data)
        
        # Check if all parameters received
        if self._parameters_received >= self._parameter_count and self._parameter_count > 0:
            self._emit_event(MAVLinkEventType.ALL_PARAMETERS_RECEIVED, self._parameters.copy())
    
    def _handle_command_ack(self, msg):
        """Handle COMMAND_ACK message"""
        data = {
            'command': msg.command,
            'result': msg.result,
            'progress': getattr(msg, 'progress', None),
            'result_param2': getattr(msg, 'result_param2', None),
            'target_system': getattr(msg, 'target_system', None),
            'target_component': getattr(msg, 'target_component', None)
        }
        
        self._emit_event(MAVLinkEventType.COMMAND_ACK, data)
    
    # Mission Protocol Handlers
    def _handle_mission_count(self, msg):
        """Handle MISSION_COUNT message"""
        self._mission_count = msg.count
        self._mission_items = []
        
        data = {'count': msg.count}
        self._emit_event(MAVLinkEventType.MISSION_COUNT, data)
    
    def _handle_mission_item_int(self, msg):
        """Handle MISSION_ITEM_INT message"""
        item_data = {
            'seq': msg.seq,
            'frame': msg.frame,
            'command': msg.command,
            'current': msg.current,
            'autocontinue': msg.autocontinue,
            'param1': msg.param1,
            'param2': msg.param2,
            'param3': msg.param3,
            'param4': msg.param4,
            'x': msg.x,
            'y': msg.y,
            'z': msg.z,
            'mission_type': msg.mission_type
        }
        
        # Store mission item
        while len(self._mission_items) <= msg.seq:
            self._mission_items.append({})
        self._mission_items[msg.seq] = item_data
        
        self._emit_event(MAVLinkEventType.MISSION_ITEM, item_data)
        
        # Check if mission download complete
        if len([item for item in self._mission_items if item]) >= self._mission_count:
            self._emit_event(MAVLinkEventType.MISSION_DOWNLOAD_COMPLETE, {
                'items': self._mission_items,
                'count': self._mission_count
            })
    
    def _handle_mission_item(self, msg):
        """Handle legacy MISSION_ITEM message"""
        item_data = {
            'seq': msg.seq,
            'frame': msg.frame,
            'command': msg.command,
            'current': msg.current,
            'autocontinue': msg.autocontinue,
            'param1': msg.param1,
            'param2': msg.param2,
            'param3': msg.param3,
            'param4': msg.param4,
            'x': msg.x,
            'y': msg.y,
            'z': msg.z,
            'mission_type': getattr(msg, 'mission_type', 0)
        }
        
        # Store mission item
        while len(self._mission_items) <= msg.seq:
            self._mission_items.append({})
        self._mission_items[msg.seq] = item_data
        
        self._emit_event(MAVLinkEventType.MISSION_ITEM, item_data)
    
    def _handle_mission_ack(self, msg):
        """Handle MISSION_ACK message"""
        data = {
            'type': msg.type,
            'mission_type': getattr(msg, 'mission_type', 0),
            'target_system': msg.target_system,
            'target_component': msg.target_component
        }
        
        self._emit_event(MAVLinkEventType.MISSION_ACK, data)
    
    def _handle_mission_current(self, msg):
        """Handle MISSION_CURRENT message"""
        self._current_mission_seq = msg.seq
        
        data = {
            'seq': msg.seq,
            'total': getattr(msg, 'total', self._mission_count),
            'mission_state': getattr(msg, 'mission_state', 0),
            'mission_mode': getattr(msg, 'mission_mode', 0)
        }
        
        self._emit_event(MAVLinkEventType.MISSION_CURRENT, data)
    
    def _handle_mission_item_reached(self, msg):
        """Handle MISSION_ITEM_REACHED message"""
        data = {'seq': msg.seq}
        self._emit_event(MAVLinkEventType.MISSION_ITEM_REACHED, data)
    
    def _handle_home_position(self, msg):
        """Handle HOME_POSITION message"""
        data = {
            'lat': msg.latitude / 1e7,
            'lon': msg.longitude / 1e7,
            'alt': msg.altitude / 1000.0,
            'x': msg.x,
            'y': msg.y,
            'z': msg.z,
            'q': [msg.q[0], msg.q[1], msg.q[2], msg.q[3]],
            'approach_x': msg.approach_x,
            'approach_y': msg.approach_y,
            'approach_z': msg.approach_z,
            'time_usec': msg.time_usec,
            'source': 'HOME_POSITION'
        }
        
        self._emit_event(MAVLinkEventType.HOME_POSITION, data)
    
    def _get_flight_mode_name(self, custom_mode: int) -> str:
        """Get flight mode name from custom mode"""
        # ArduPilot flight mode mapping
        ardupilot_modes = {
            0: 'MANUAL', 1: 'CIRCLE', 2: 'STABILIZE', 3: 'TRAINING',
            4: 'ACRO', 5: 'FLY_BY_WIRE_A', 6: 'FLY_BY_WIRE_B',
            7: 'CRUISE', 8: 'AUTOTUNE', 9: 'AUTO', 10: 'RTL',
            11: 'LOITER', 12: 'TAKEOFF', 13: 'LAND', 14: 'GUIDED',
            15: 'INITIALISING', 16: 'QSTABILIZE', 17: 'QHOVER',
            18: 'QLOITER', 19: 'QLAND', 20: 'QRTL', 21: 'QTAKEOFF',
            22: 'QAUTOTUNE', 23: 'QACRO'
        }
        
        return ardupilot_modes.get(custom_mode, f'UNKNOWN({custom_mode})')
    
    def _attempt_reconnection(self):
        """Attempt to reconnect to vehicle"""
        if self._reconnect_count >= self._max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self._set_connection_state(MAVLinkConnectionState.ERROR)
            return
        
        self._reconnect_count += 1
        logger.info(f"Attempting reconnection {self._reconnect_count}/{self._max_reconnect_attempts}")
        
        time.sleep(self._reconnect_delay)
        
        if not self._should_stop and self._auto_reconnect:
            if self.connect(self._connection_port, self._connection_baud):
                logger.info("Reconnection successful")
            else:
                logger.warning("Reconnection failed, will retry")
    
    def _emit_event(self, event_type: MAVLinkEventType, data: Any):
        """Emit event to listeners"""
        event = MAVLinkEvent(event_type, data)
        
        # Call registered listeners
        if event_type in self._event_listeners:
            for callback in self._event_listeners[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Event listener error: {e}")
        
        # Add to event queue for stream-like access
        self._event_queue.put(event)
    
    def add_event_listener(self, event_type: MAVLinkEventType, callback: Callable):
        """Add event listener for specific event type"""
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(callback)
    
    def remove_event_listener(self, event_type: MAVLinkEventType, callback: Callable):
        """Remove event listener"""
        if event_type in self._event_listeners:
            try:
                self._event_listeners[event_type].remove(callback)
            except ValueError:
                pass
    
    def get_events(self, block: bool = False, timeout: Optional[float] = None) -> Optional[MAVLinkEvent]:
        """Get next event from queue"""
        try:
            return self._event_queue.get(block=block, timeout=timeout)
        except:
            return None
    
    # ===== HIGH-LEVEL API METHODS =====
    
    # Data Stream Methods
    def request_all_data_streams(self, rate_hz: int = 4) -> bool:
        """Request all MAVLink data streams"""
        if self._data_stream_handler:
            return self._data_stream_handler.request_all_data_streams(rate_hz)
        return False
    
    def request_attitude_stream(self, rate_hz: int = 10) -> bool:
        """Request attitude data stream"""
        if self._data_stream_handler:
            return self._data_stream_handler.request_attitude_stream(rate_hz)
        return False
    
    def request_position_stream(self, rate_hz: int = 3) -> bool:
        """Request position data stream"""
        if self._data_stream_handler:
            return self._data_stream_handler.request_position_stream(rate_hz)
        return False
    
    def request_vfr_hud_stream(self, rate_hz: int = 5) -> bool:
        """Request VFR HUD data stream"""
        if self._data_stream_handler:
            return self._data_stream_handler.request_vfr_hud_stream(rate_hz)
        return False
    
    def configure_standard_streams(self) -> bool:
        """Configure standard data streams"""
        if self._data_stream_handler:
            return self._data_stream_handler.configure_standard_streams()
        return False
    
    def set_stream_rate(self, message_name: str, rate_hz: int) -> bool:
        """Set individual message stream rate"""
        if self._data_stream_handler:
            return self._data_stream_handler.set_stream_rate(message_name, rate_hz)
        return False
    
    # Parameter Methods
    def request_all_parameters(self) -> bool:
        """Request all parameters from vehicle"""
        if self._parameter_handler:
            return self._parameter_handler.request_parameter_list()
        return False
    
    def request_parameter(self, param_name: str) -> bool:
        """Request specific parameter"""
        if self._parameter_handler:
            return self._parameter_handler.request_parameter(param_name)
        return False
    
    def set_parameter(self, param_name: str, param_value: float) -> bool:
        """Set parameter value"""
        if self._parameter_handler:
            param_type = self._parameter_handler.get_parameter_type_from_value(param_value)
            return self._parameter_handler.set_parameter(param_name, param_value, param_type)
        return False
    
    # Command Methods
    def send_arm_command(self, arm: bool, force: bool = False) -> bool:
        """Send arm/disarm command"""
        if self._command_handler:
            return self._command_handler.send_arm_command(arm, force)
        return False
    
    def arm(self, force: bool = False) -> bool:
        """Arm the vehicle"""
        return self.send_arm_command(True, force)
    
    def disarm(self, force: bool = False) -> bool:
        """Disarm the vehicle"""
        return self.send_arm_command(False, force)
    
    def set_flight_mode(self, mode_number: int) -> bool:
        """Set ArduPilot flight mode by number"""
        if self._command_handler:
            return self._command_handler.set_ardupilot_mode(mode_number)
        return False
    
    def takeoff(self, altitude: float, pitch: float = 0.0, yaw: float = 0.0) -> bool:
        """Command takeoff"""
        if self._command_handler:
            return self._command_handler.takeoff(altitude, pitch, yaw)
        return False
    
    def land(self, lat: float = 0.0, lon: float = 0.0, alt: float = 0.0) -> bool:
        """Command land"""
        if self._command_handler:
            return self._command_handler.land(yaw=float('nan'), lat=lat, lon=lon, alt=alt)
        return False
    
    def return_to_launch(self) -> bool:
        """Command return to launch"""
        if self._command_handler:
            return self._command_handler.return_to_launch()
        return False
    
    def goto_position(self, lat: float, lon: float, alt: float, yaw: float = float('nan')) -> bool:
        """Go to specific position"""
        if self._command_handler:
            return self._command_handler.goto_position(lat, lon, alt, yaw=yaw)
        return False
    
    # Mission Methods
    def request_mission_list(self) -> bool:
        """Request mission list from vehicle"""
        if self._mission_handler:
            return self._mission_handler.request_mission_list()
        return False
    
    def request_mission_item(self, seq: int) -> bool:
        """Request specific mission item"""
        if self._mission_handler:
            return self._mission_handler.request_mission_item(seq)
        return False
    
    def start_mission_upload(self, items: List[Dict[str, Any]]) -> bool:
        """Start mission upload process"""
        if self._mission_handler:
            # Convert dict items to MissionItem objects
            from .handlers.mission_handler import MissionItem
            mission_items = []
            for item in items:
                mission_items.append(MissionItem(
                    seq=item.get('seq', 0),
                    frame=item.get('frame', mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT),
                    command=item.get('command', mavlink.MAV_CMD_NAV_WAYPOINT),
                    current=item.get('current', 0),
                    autocontinue=item.get('autocontinue', 1),
                    param1=item.get('param1', 0.0),
                    param2=item.get('param2', 0.0),
                    param3=item.get('param3', 0.0),
                    param4=item.get('param4', 0.0),
                    x=item.get('x', 0.0),
                    y=item.get('y', 0.0),
                    z=item.get('z', 0.0),
                    mission_type=item.get('mission_type', 0)
                ))
            return self._mission_handler.start_mission_upload(mission_items)
        return False
    
    def clear_mission(self) -> bool:
        """Clear all missions on vehicle"""
        if self._mission_handler:
            return self._mission_handler.clear_mission()
        return False
    
    def set_current_mission_item(self, seq: int) -> bool:
        """Set current mission item"""
        if self._mission_handler:
            return self._mission_handler.set_current_mission_item(seq)
        return False
    
    def request_home_position(self) -> bool:
        """Request home position"""
        if self._mission_handler:
            return self._mission_handler.request_home_position()
        return False
    
    # Convenience methods for mission creation
    def create_simple_mission(self, waypoints: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Create simple waypoint mission
        
        Args:
            waypoints: List of waypoint dicts with 'lat', 'lon', 'alt' keys
            
        Returns:
            List of mission items ready for upload
        """
        items = []
        for i, wp in enumerate(waypoints):
            if self._mission_handler:
                item = self._mission_handler.create_waypoint_item(
                    seq=i,
                    lat=wp['lat'],
                    lon=wp['lon'],
                    alt=wp['alt'],
                    hold_time=wp.get('hold_time', 0.0),
                    yaw=wp.get('yaw', float('nan'))
                )
                items.append(item.to_dict())
        return items
    
    # Vehicle State Access Methods
    def get_attitude(self) -> Dict[str, float]:
        """Get current attitude data"""
        with self._lock:
            return {
                'roll': self._vehicle_data.get('roll', 0.0),
                'pitch': self._vehicle_data.get('pitch', 0.0),
                'yaw': self._vehicle_data.get('yaw', 0.0),
                'rollspeed': self._vehicle_data.get('rollspeed', 0.0),
                'pitchspeed': self._vehicle_data.get('pitchspeed', 0.0),
                'yawspeed': self._vehicle_data.get('yawspeed', 0.0)
            }
    
    def get_position(self) -> Dict[str, float]:
        """Get current position data"""
        with self._lock:
            return {
                'lat': self._vehicle_data.get('lat', 0.0),
                'lon': self._vehicle_data.get('lon', 0.0),
                'alt': self._vehicle_data.get('alt', 0.0),
                'relative_alt': self._vehicle_data.get('relative_alt', 0.0)
            }
    
    def get_velocity(self) -> Dict[str, float]:
        """Get current velocity data"""
        with self._lock:
            return {
                'vx': self._vehicle_data.get('vx', 0.0),
                'vy': self._vehicle_data.get('vy', 0.0),
                'vz': self._vehicle_data.get('vz', 0.0),
                'groundspeed': self._vehicle_data.get('groundspeed', 0.0),
                'airspeed': self._vehicle_data.get('airspeed', 0.0)
            }
    
    def get_battery_status(self) -> Dict[str, Any]:
        """Get current battery status"""
        with self._lock:
            battery = self._vehicle_data.get('battery', {})
            return {
                'voltage': battery.get('voltages', [0])[0] if battery.get('voltages') else 0.0,
                'current': battery.get('current_battery', 0.0),
                'remaining': battery.get('battery_remaining', -1),
                'consumed': battery.get('current_consumed', 0),
                'temperature': battery.get('temperature', 0.0)
            }
    
    def get_gps_info(self) -> Dict[str, Any]:
        """Get GPS information"""
        with self._lock:
            gps = self._vehicle_data.get('gps', {})
            return {
                'fix_type': gps.get('fix_type', 0),
                'satellites': gps.get('satellites_visible', 0),
                'hdop': gps.get('eph', 99.99),
                'vdop': gps.get('epv', 99.99),
                'lat': gps.get('lat', None),
                'lon': gps.get('lon', None),
                'alt': gps.get('alt', None)
            }
    
    def get_flight_mode(self) -> str:
        """Get current flight mode"""
        with self._lock:
            return self._vehicle_data.get('mode', 'UNKNOWN')
    
    def is_armed(self) -> bool:
        """Check if vehicle is armed"""
        with self._lock:
            return self._vehicle_data.get('armed', False)
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all vehicle data"""
        with self._lock:
            return {
                'attitude': self.get_attitude(),
                'position': self.get_position(),
                'velocity': self.get_velocity(),
                'battery': self.get_battery_status(),
                'gps': self.get_gps_info(),
                'mode': self.get_flight_mode(),
                'armed': self.is_armed(),
                'connection_state': self._connection_state.value,
                'parameters': self._parameters.copy()
            }
    
    def dispose(self):
        """Clean up resources"""
        self.disconnect()
        
        # Clear event listeners
        self._event_listeners.clear()
        
        # Clear event queue
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except:
                break
