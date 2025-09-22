"""
DroneController - High-level Python API for Drone Control and Monitoring

This module provides a simplified, high-level interface for drone operations
built on top of the comprehensive DroneMAVLinkAPI.

Features:
- Easy connection management
- Simplified command interface
- Real-time data access
- Event-driven monitoring
- Mission management
- Parameter control

Usage:
    from Call_API import DroneController
    
    # Simple usage
    drone = DroneController()
    if drone.connect('/dev/ttyACM0'):
        attitude = drone.get_attitude()
        drone.arm()
        drone.takeoff(10)
        drone.disconnect()
    
    # Context manager usage  
    with DroneController() as drone:
        if drone.connect('/dev/ttyACM0'):
            # Your operations here
            pass
"""

from .mavlink import DroneMAVLinkAPI, MAVLinkEventType, MAVLinkEvent, MAVLinkConnectionState
import logging
import time
import threading
import json
from typing import Dict, Any, Optional, Callable, List

# Setup logging
logger = logging.getLogger(__name__)

class DroneController:
    """
    High-level drone controller interface
    Provides a simplified API for common drone operations
    """
    
    def __init__(self, connection_string: str = '/dev/ttyACM0', baud_rate: int = 115200):
        """
        Initialize drone controller
        
        Args:
            connection_string: Serial port or connection string
            baud_rate: Baud rate for serial communication
        """
        self.connection_string = connection_string
        self.baud_rate = baud_rate
        
        # Create the MAVLink API instance
        self.api = DroneMAVLinkAPI()
        
        # Connection status
        self._connected = False
        
        # Cache for latest data
        self._attitude = {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
        self._position = {'lat': 0.0, 'lon': 0.0, 'alt': 0.0}
        self._velocity = {'vx': 0.0, 'vy': 0.0, 'vz': 0.0, 'groundspeed': 0.0}
        self._battery = {'voltage': 0.0, 'current': 0.0, 'remaining': -1}
        self._gps = {'fix_type': 0, 'satellites': 0, 'hdop': 99.99}
        self._flight_mode = 'UNKNOWN'
        self._armed = False
        
        # Setup event listeners
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Setup event listeners to cache latest data"""
        self.api.add_event_listener(MAVLinkEventType.HEARTBEAT, self._on_heartbeat)
        self.api.add_event_listener(MAVLinkEventType.ATTITUDE, self._on_attitude)
        self.api.add_event_listener(MAVLinkEventType.POSITION, self._on_position)
        self.api.add_event_listener(MAVLinkEventType.VFR_HUD, self._on_velocity)
        self.api.add_event_listener(MAVLinkEventType.BATTERY_STATUS, self._on_battery)
        self.api.add_event_listener(MAVLinkEventType.GPS_INFO, self._on_gps)
        self.api.add_event_listener(MAVLinkEventType.CONNECTION_STATE_CHANGED, self._on_connection_changed)
    
    def _on_connection_changed(self, event: MAVLinkEvent):
        """Handle connection state changes"""
        self._connected = (event.data == MAVLinkConnectionState.CONNECTED)
        if self._connected:
            self.api.configure_standard_streams()
    
    def _on_heartbeat(self, event: MAVLinkEvent):
        """Update heartbeat data"""
        data = event.data
        self._armed = data.get('armed', False)
        self._flight_mode = data.get('mode', 'UNKNOWN')
    
    def _on_attitude(self, event: MAVLinkEvent):
        """Update attitude data"""
        self._attitude = event.data
    
    def _on_position(self, event: MAVLinkEvent):
        """Update position data"""
        self._position = event.data
    
    def _on_velocity(self, event: MAVLinkEvent):
        """Update velocity data"""
        data = event.data
        self._velocity.update({
            'groundspeed': data.get('groundspeed', 0),
            'airspeed': data.get('airspeed', 0),
            'climb': data.get('climb', 0)
        })
    
    def _on_battery(self, event: MAVLinkEvent):
        """Update battery data"""
        data = event.data
        self._battery.update({
            'voltage': data.get('voltages', [0])[0] if data.get('voltages') else 0,
            'current': data.get('current_battery', 0),
            'remaining': data.get('battery_remaining', -1)
        })
    
    def _on_gps(self, event: MAVLinkEvent):
        """Update GPS data"""
        self._gps = event.data
    
    # =================== Connection Methods ===================
    
    def connect(self, connection_string: str = None, baud_rate: int = None) -> bool:
        """
        Connect to drone
        
        Args:
            connection_string: Override default connection string
            baud_rate: Override default baud rate
            
        Returns:
            bool: True if connected successfully
        """
        conn_str = connection_string or self.connection_string
        baud = baud_rate or self.baud_rate
        
        logger.info(f"Connecting to drone at {conn_str}...")
        
        if self.api.connect(conn_str, baud):
            # Wait for initial connection
            timeout = 10
            start_time = time.time()
            while not self._connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self._connected:
                logger.info("Connected successfully!")
                return True
            else:
                logger.error("Connection timeout - no heartbeat received")
                return False
        else:
            logger.error("Failed to establish connection")
            return False
    
    def disconnect(self):
        """Disconnect from drone"""
        if self.api:
            self.api.dispose()
        self._connected = False
        logger.info("Disconnected from drone")
    
    def is_connected(self) -> bool:
        """Check if connected to drone"""
        return self._connected
    
    # =================== Data Access Methods ===================
    
    def get_attitude(self) -> Dict[str, float]:
        """Get current attitude (roll, pitch, yaw)"""
        return self._attitude.copy()
    
    def get_position(self) -> Dict[str, float]:
        """Get current GPS position"""
        return self._position.copy()
    
    def get_velocity(self) -> Dict[str, float]:
        """Get current velocity information"""
        return self._velocity.copy()
    
    def get_battery_status(self) -> Dict[str, float]:
        """Get battery status"""
        return self._battery.copy()
    
    def get_gps_info(self) -> Dict[str, Any]:
        """Get GPS information"""
        return self._gps.copy()
    
    def get_flight_mode(self) -> str:
        """Get current flight mode"""
        return self._flight_mode
    
    def is_armed(self) -> bool:
        """Check if vehicle is armed"""
        return self._armed
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all cached vehicle data"""
        return {
            'attitude': self.get_attitude(),
            'position': self.get_position(), 
            'velocity': self.get_velocity(),
            'battery': self.get_battery_status(),
            'gps': self.get_gps_info(),
            'flight_mode': self.get_flight_mode(),
            'armed': self.is_armed(),
            'connected': self.is_connected()
        }
    
    # =================== JSON Data Methods ===================
    
    def get_all_data_json(self) -> str:
        """
        Get all vehicle data in JSON format
        
        Returns:
            str: JSON string containing all vehicle data
        """
        import json
        data = self.get_all_data()
        return json.dumps(data, indent=2, default=str)
    
    def get_attitude_json(self) -> str:
        """
        Get attitude data in JSON format
        
        Returns:
            str: JSON string containing roll, pitch, yaw data
        """
        import json
        return json.dumps(self.get_attitude(), indent=2)
    
    def get_position_json(self) -> str:
        """
        Get position data in JSON format
        
        Returns:
            str: JSON string containing latitude, longitude, altitude
        """
        import json
        return json.dumps(self.get_position(), indent=2)
    
    def get_velocity_json(self) -> str:
        """
        Get velocity data in JSON format
        
        Returns:
            str: JSON string containing velocity components and speeds
        """
        import json
        return json.dumps(self.get_velocity(), indent=2)
    
    def get_battery_status_json(self) -> str:
        """
        Get battery status in JSON format
        
        Returns:
            str: JSON string containing battery voltage, current, remaining percentage
        """
        import json
        return json.dumps(self.get_battery_status(), indent=2)
    
    def get_gps_info_json(self) -> str:
        """
        Get GPS information in JSON format
        
        Returns:
            str: JSON string containing GPS fix type, satellites, HDOP
        """
        import json
        return json.dumps(self.get_gps_info(), indent=2, default=str)
    
    def get_flight_status_json(self) -> str:
        """
        Get flight status in JSON format
        
        Returns:
            str: JSON string containing flight mode, armed status, connection
        """
        import json
        status = {
            'flight_mode': self.get_flight_mode(),
            'armed': self.is_armed(),
            'connected': self.is_connected()
        }
        return json.dumps(status, indent=2)
    
    def get_telemetry_stream_json(self) -> str:
        """
        Get complete telemetry stream in JSON format
        Includes all sensor data with timestamps
        
        Returns:
            str: JSON string containing comprehensive telemetry data
        """
        import json
        from datetime import datetime
        
        telemetry = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'connected': self.is_connected(),
                'flight_mode': self.get_flight_mode(),
                'armed': self.is_armed()
            },
            'attitude': self.get_attitude(),
            'position': self.get_position(),
            'velocity': self.get_velocity(),
            'battery': self.get_battery_status(),
            'gps': self.get_gps_info()
        }
        return json.dumps(telemetry, indent=2, default=str)
    
    def get_datastream_summary_json(self) -> str:
        """
        Get datastream summary with data freshness indicators
        
        Returns:
            str: JSON string with data summary and status indicators
        """
        import json
        from datetime import datetime
        
        current_time = datetime.now()
        
        summary = {
            'data_summary': {
                'total_parameters': 8,
                'connection_status': 'connected' if self.is_connected() else 'disconnected',
                'last_update': current_time.isoformat(),
                'data_streams': {
                    'attitude': {
                        'available': bool(self._attitude['roll'] or self._attitude['pitch'] or self._attitude['yaw']),
                        'roll': self._attitude['roll'],
                        'pitch': self._attitude['pitch'],
                        'yaw': self._attitude['yaw']
                    },
                    'position': {
                        'available': bool(self._position['lat'] or self._position['lon']),
                        'latitude': self._position['lat'],
                        'longitude': self._position['lon'],
                        'altitude': self._position['alt']
                    },
                    'velocity': {
                        'available': bool(self._velocity['groundspeed']),
                        'ground_speed': self._velocity['groundspeed'],
                        'air_speed': self._velocity.get('airspeed', 0),
                        'climb_rate': self._velocity.get('climb', 0)
                    },
                    'battery': {
                        'available': bool(self._battery['voltage']),
                        'voltage': self._battery['voltage'],
                        'current': self._battery['current'],
                        'remaining_percent': self._battery['remaining']
                    },
                    'gps': {
                        'available': bool(self._gps['fix_type'] > 0),
                        'fix_type': self._gps['fix_type'],
                        'satellites': self._gps['satellites'],
                        'hdop': self._gps['hdop']
                    },
                    'flight_status': {
                        'mode': self._flight_mode,
                        'armed': self._armed
                    }
                }
            }
        }
        return json.dumps(summary, indent=2, default=str)
    
    # =================== Command Methods ===================
    
    def arm(self, force: bool = False) -> bool:
        """
        Arm the vehicle
        
        Args:
            force: Force arming even if pre-arm checks fail
            
        Returns:
            bool: True if command sent successfully
        """
        if not self._connected:
            logger.error("Cannot arm - not connected")
            return False
        
        logger.info("Sending arm command...")
        return self.api.arm_disarm(True, force)
    
    def disarm(self, force: bool = False) -> bool:
        """
        Disarm the vehicle
        
        Args:
            force: Force disarming
            
        Returns:
            bool: True if command sent successfully
        """
        if not self._connected:
            logger.error("Cannot disarm - not connected")
            return False
        
        logger.info("Sending disarm command...")
        return self.api.arm_disarm(False, force)
    
    def set_mode(self, mode: str) -> bool:
        """
        Set flight mode
        
        Args:
            mode: Flight mode name (e.g., 'GUIDED', 'AUTO', 'RTL')
            
        Returns:
            bool: True if command sent successfully
        """
        if not self._connected:
            logger.error("Cannot set mode - not connected")
            return False
        
        logger.info(f"Setting flight mode to {mode}...")
        return self.api.set_mode(mode)
    
    def takeoff(self, altitude: float, yaw: float = 0.0) -> bool:
        """
        Command takeoff
        
        Args:
            altitude: Target altitude in meters
            yaw: Target yaw angle in degrees
            
        Returns:
            bool: True if command sent successfully
        """
        if not self._connected:
            logger.error("Cannot takeoff - not connected")
            return False
        
        if not self._armed:
            logger.warning("Vehicle not armed - arming first...")
            if not self.arm():
                logger.error("Failed to arm vehicle")
                return False
            time.sleep(2)  # Wait for arming
        
        logger.info(f"Commanding takeoff to {altitude}m...")
        return self.api.takeoff(altitude, yaw)
    
    def land(self, lat: float = 0.0, lon: float = 0.0) -> bool:
        """
        Command landing
        
        Args:
            lat: Target latitude (0 = current position)
            lon: Target longitude (0 = current position)
            
        Returns:
            bool: True if command sent successfully
        """
        if not self._connected:
            logger.error("Cannot land - not connected")
            return False
        
        logger.info("Commanding landing...")
        return self.api.land(lat, lon)
    
    def return_to_launch(self) -> bool:
        """
        Return to launch position
        
        Returns:
            bool: True if command sent successfully
        """
        if not self._connected:
            logger.error("Cannot RTL - not connected")
            return False
        
        logger.info("Commanding return to launch...")
        return self.api.return_to_launch()
    
    def goto_position(self, lat: float, lon: float, alt: float, yaw: float = 0.0) -> bool:
        """
        Go to specific position
        
        Args:
            lat: Target latitude
            lon: Target longitude  
            alt: Target altitude
            yaw: Target yaw angle
            
        Returns:
            bool: True if command sent successfully
        """
        if not self._connected:
            logger.error("Cannot goto position - not connected")
            return False
        
        logger.info(f"Going to position: {lat}, {lon}, {alt}m")
        return self.api.goto_position(lat, lon, alt, yaw)
    
    # =================== Parameter Methods ===================
    
    def get_parameter(self, param_name: str) -> Optional[float]:
        """
        Get parameter value
        
        Args:
            param_name: Parameter name
            
        Returns:
            Parameter value or None if not found
        """
        if not hasattr(self.api, 'parameters'):
            return None
        return self.api.parameters.get(param_name)
    
    def set_parameter(self, param_name: str, value: float) -> bool:
        """
        Set parameter value
        
        Args:
            param_name: Parameter name
            value: Parameter value
            
        Returns:
            bool: True if command sent successfully
        """
        if not self._connected:
            logger.error("Cannot set parameter - not connected")
            return False
        
        logger.info(f"Setting parameter {param_name} = {value}")
        return self.api.set_parameter(param_name, value)
    
    def request_all_parameters(self) -> bool:
        """
        Request all parameters from vehicle
        
        Returns:
            bool: True if request sent successfully
        """
        if not self._connected:
            logger.error("Cannot request parameters - not connected")
            return False
        
        logger.info("Requesting all parameters...")
        return self.api.request_all_parameters()
    
    def get_parameters_json(self) -> str:
        """
        Get all vehicle parameters in JSON format
        
        Returns:
            str: JSON string containing all available parameters
        """
        import json
        
        if hasattr(self.api, 'parameters') and self.api.parameters:
            return json.dumps(self.api.parameters, indent=2, sort_keys=True)
        else:
            return json.dumps({
                "status": "no_parameters",
                "message": "Parameters not available. Call request_all_parameters() first."
            }, indent=2)
    
    def get_system_status_json(self) -> str:
        """
        Get comprehensive system status in JSON format
        
        Returns:
            str: JSON string with detailed system information
        """
        import json
        from datetime import datetime
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'system_status': {
                'connection': {
                    'connected': self.is_connected(),
                    'connection_string': self.connection_string,
                    'baud_rate': self.baud_rate
                },
                'flight_controller': {
                    'flight_mode': self.get_flight_mode(),
                    'armed': self.is_armed()
                },
                'sensors': {
                    'attitude': {
                        'roll_deg': round(self._attitude['roll'] * 57.2958, 2),  # Convert to degrees
                        'pitch_deg': round(self._attitude['pitch'] * 57.2958, 2),
                        'yaw_deg': round(self._attitude['yaw'] * 57.2958, 2)
                    },
                    'position': {
                        'latitude': self._position['lat'],
                        'longitude': self._position['lon'],
                        'altitude_m': self._position['alt'],
                        'has_position': bool(self._position['lat'] or self._position['lon'])
                    },
                    'velocity': {
                        'ground_speed_ms': self._velocity['groundspeed'],
                        'air_speed_ms': self._velocity.get('airspeed', 0),
                        'climb_rate_ms': self._velocity.get('climb', 0)
                    },
                    'power': {
                        'battery_voltage': self._battery['voltage'],
                        'battery_current': self._battery['current'],
                        'battery_remaining_percent': self._battery['remaining'],
                        'low_battery': self._battery['remaining'] < 20 if self._battery['remaining'] >= 0 else False
                    },
                    'gps': {
                        'fix_type': self._gps['fix_type'],
                        'satellites_visible': self._gps['satellites'],
                        'horizontal_dilution': self._gps['hdop'],
                        'gps_healthy': self._gps['fix_type'] >= 3
                    }
                },
                'health_indicators': {
                    'overall_health': self._get_overall_health(),
                    'warnings': self._get_system_warnings()
                }
            }
        }
        return json.dumps(status, indent=2, default=str)
    
    def _get_overall_health(self) -> str:
        """Get overall system health status"""
        if not self.is_connected():
            return "disconnected"
        elif self._battery['remaining'] < 20 and self._battery['remaining'] >= 0:
            return "warning_low_battery"
        elif self._gps['fix_type'] < 3:
            return "warning_no_gps"
        else:
            return "healthy"
    
    def _get_system_warnings(self) -> List[str]:
        """Get list of current system warnings"""
        warnings = []
        
        if not self.is_connected():
            warnings.append("Vehicle not connected")
        
        if self._battery['remaining'] < 20 and self._battery['remaining'] >= 0:
            warnings.append(f"Low battery: {self._battery['remaining']}%")
        
        if self._gps['fix_type'] < 3:
            warnings.append(f"Poor GPS fix: type {self._gps['fix_type']}")
        
        if self._gps['satellites'] < 6:
            warnings.append(f"Low satellite count: {self._gps['satellites']}")
        
        return warnings
    
    def get_live_telemetry_json(self, include_timestamp: bool = True) -> str:
        """
        Get live telemetry data optimized for real-time streaming
        
        Args:
            include_timestamp: Whether to include timestamp in output
            
        Returns:
            str: Compact JSON string with current telemetry
        """
        import json
        from datetime import datetime
        
        telemetry = {
            'att': {  # Attitude
                'r': round(self._attitude['roll'] * 57.2958, 1),    # Roll in degrees
                'p': round(self._attitude['pitch'] * 57.2958, 1),  # Pitch in degrees  
                'y': round(self._attitude['yaw'] * 57.2958, 1)     # Yaw in degrees
            },
            'pos': {  # Position
                'lat': self._position['lat'],
                'lon': self._position['lon'], 
                'alt': round(self._position['alt'], 1)
            },
            'vel': {  # Velocity
                'gs': round(self._velocity['groundspeed'], 1),  # Ground speed
                'vs': round(self._velocity.get('climb', 0), 1)  # Vertical speed
            },
            'bat': {  # Battery
                'v': round(self._battery['voltage'], 1),
                'i': round(self._battery['current'], 1),
                'r': self._battery['remaining']
            },
            'gps': {  # GPS
                'fix': self._gps['fix_type'],
                'sat': self._gps['satellites']
            },
            'stat': {  # Status
                'mode': self._flight_mode,
                'armed': self._armed,
                'conn': self.is_connected()
            }
        }
        
        if include_timestamp:
            telemetry['ts'] = datetime.now().isoformat()
        
        return json.dumps(telemetry, separators=(',', ':'))  # Compact JSON
    
    # =================== Event Methods ===================
    
    def add_event_listener(self, event_type: MAVLinkEventType, callback: Callable):
        """
        Add event listener
        
        Args:
            event_type: Type of event to listen for
            callback: Callback function to call when event occurs
        """
        self.api.add_event_listener(event_type, callback)
    
    def remove_event_listener(self, event_type: MAVLinkEventType, callback: Callable):
        """
        Remove event listener
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        self.api.remove_event_listener(event_type, callback)
    
    # =================== Mission Methods ===================
    
    def upload_simple_mission(self, waypoints: List[Dict[str, float]]) -> bool:
        """
        Upload a simple waypoint mission
        
        Args:
            waypoints: List of waypoint dictionaries with 'lat', 'lon', 'alt' keys
            
        Returns:
            bool: True if upload started successfully
        """
        if not self._connected:
            logger.error("Cannot upload mission - not connected")
            return False
        
        # Convert simple waypoints to mission items
        mission_items = []
        
        # Add takeoff item
        mission_items.append({
            'seq': 0,
            'frame': 0,  # MAV_FRAME_GLOBAL
            'command': 22,  # MAV_CMD_NAV_TAKEOFF
            'current': 1,
            'autocontinue': 1,
            'param1': 0, 'param2': 0, 'param3': 0, 'param4': 0,
            'x': 0, 'y': 0, 'z': waypoints[0]['alt'] if waypoints else 10,
            'mission_type': 0
        })
        
        # Add waypoints
        for i, wp in enumerate(waypoints):
            mission_items.append({
                'seq': i + 1,
                'frame': 0,
                'command': 16,  # MAV_CMD_NAV_WAYPOINT
                'current': 0,
                'autocontinue': 1,
                'param1': 0, 'param2': 0, 'param3': 0, 'param4': 0,
                'x': wp['lat'], 'y': wp['lon'], 'z': wp['alt'],
                'mission_type': 0
            })
        
        # Add land item
        if waypoints:
            last_wp = waypoints[-1]
            mission_items.append({
                'seq': len(waypoints) + 1,
                'frame': 0,
                'command': 21,  # MAV_CMD_NAV_LAND
                'current': 0,
                'autocontinue': 1,
                'param1': 0, 'param2': 0, 'param3': 0, 'param4': 0,
                'x': last_wp['lat'], 'y': last_wp['lon'], 'z': 0,
                'mission_type': 0
            })
        
        logger.info(f"Uploading mission with {len(mission_items)} items...")
        return self.api.upload_mission(mission_items)
    
    def clear_mission(self) -> bool:
        """
        Clear current mission
        
        Returns:
            bool: True if command sent successfully
        """
        if not self._connected:
            logger.error("Cannot clear mission - not connected")
            return False
        
        logger.info("Clearing mission...")
        return self.api.clear_mission()
    
    def request_mission_list(self) -> bool:
        """
        Request current mission from vehicle
        
        Returns:
            bool: True if request sent successfully
        """
        if not self._connected:
            logger.error("Cannot request mission - not connected")
            return False
        
        logger.info("Requesting mission list...")
        return self.api.request_mission_list()
    
    # =================== Context Manager Support ===================
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

# Make the DroneController available when importing this module directly
__all__ = ['DroneController']
