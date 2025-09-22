# DroneMAVLinkAPI - Python MAVLink Library

A comprehensive, modular Python library for communicating with MAVLink-compatible drones and flight controllers.

## Features

- **Event-driven Architecture**: Real-time event handling with 20+ event types
- **Complete MAVLink Protocol Support**: Parameters, missions, commands, telemetry
- **High-level API**: Simplified interface for common drone operations  
- **Thread-safe Operations**: Safe for multi-threaded applications
- **Auto-reconnection**: Robust connection management
- **Comprehensive Logging**: Detailed logging for debugging

## Installation

1. **Install Dependencies**
   ```bash
   cd Call_API/
   pip install -r requirements.txt
   ```

2. **Import the Library**
   ```python
   from Call_API import DroneController, DroneMAVLinkAPI, MAVLinkEventType
   ```

## Installation

### Dependencies
```bash
pip install pymavlink
```

### Quick Test
```bash
# Test JSON functionality (no dependencies required)
python test_json_simple.py

# Test module structure
python test_structure_simple.py

# Full functionality test (requires pymavlink)
python test_json_api.py
```

## Quick Start

### Simple Drone Control
```python
from Call_API import DroneController

# Create controller instance
drone = DroneController()

# Connect to drone
if drone.connect('/dev/ttyACM0', 115200):
    print("Connected!")
    
    # Get current data
    attitude = drone.get_attitude()
    position = drone.get_position()
    battery = drone.get_battery_status()
    
    print(f"Attitude: Roll={attitude['roll']:.1f}°")
    print(f"Position: {position['lat']:.6f}, {position['lon']:.6f}")
    print(f"Battery: {battery['voltage']:.1f}V, {battery['remaining']}%")
    
    # Control commands (when safe)
    if not drone.is_armed():
        drone.arm()
        drone.takeoff(10)  # Takeoff to 10 meters
    
    # Disconnect
    drone.disconnect()
```

### Context Manager Usage
```python
from Call_API import DroneController

with DroneController() as drone:
    if drone.connect('/dev/ttyACM0'):
        # Your operations here
        data = drone.get_all_data()
        print(f"Flight mode: {data['flight_mode']}")
        print(f"Armed: {data['armed']}")
        # Connection automatically closed when exiting context
```

### Event-driven Monitoring
```python
from Call_API import DroneMAVLinkAPI, MAVLinkEventType

# Create API instance for advanced usage
api = DroneMAVLinkAPI()

# Define event handlers
def on_attitude(event):
    data = event.data
    print(f"Attitude: R={data['roll']:.1f}° P={data['pitch']:.1f}° Y={data['yaw']:.1f}°")

def on_battery(event):
    data = event.data
    voltage = data.get('voltages', [0])[0] if data.get('voltages') else 0
    remaining = data.get('battery_remaining', -1)
    print(f"Battery: {voltage:.1f}V, {remaining}%")

# Register event listeners
api.add_event_listener(MAVLinkEventType.ATTITUDE, on_attitude)
api.add_event_listener(MAVLinkEventType.BATTERY_STATUS, on_battery)

# Connect and run
if api.connect('/dev/ttyACM0', 115200):
    api.configure_standard_streams()
    
    # Keep running to receive events
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        api.dispose()
```

## API Reference

### DroneController Class

High-level interface for common drone operations.

#### Connection Methods
```python
drone = DroneController()

# Connect to drone
success = drone.connect('/dev/ttyACM0', 115200)
success = drone.connect('udp:127.0.0.1:14550')  # SITL

# Check connection
is_connected = drone.is_connected()

# Disconnect
drone.disconnect()
```

#### Data Access Methods
```python
# Get vehicle data
attitude = drone.get_attitude()        # {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
position = drone.get_position()        # {'lat': 0.0, 'lon': 0.0, 'alt': 0.0}
velocity = drone.get_velocity()        # {'vx': 0.0, 'vy': 0.0, 'vz': 0.0, 'groundspeed': 0.0}
battery = drone.get_battery_status()   # {'voltage': 0.0, 'current': 0.0, 'remaining': -1}
gps = drone.get_gps_info()            # {'fix_type': 0, 'satellites': 0, 'hdop': 99.99}

# Get flight status
mode = drone.get_flight_mode()         # 'STABILIZE', 'GUIDED', etc.
armed = drone.is_armed()              # True/False

# Get all data at once
all_data = drone.get_all_data()       # Complete vehicle state
```

#### JSON Data Methods
```python
# JSON versions of all data methods - perfect for APIs and web applications
attitude_json = drone.get_attitude_json()      # JSON string with attitude data
position_json = drone.get_position_json()      # JSON string with position data
velocity_json = drone.get_velocity_json()      # JSON string with velocity data
battery_json = drone.get_battery_status_json() # JSON string with battery status
gps_json = drone.get_gps_info_json()          # JSON string with GPS data
status_json = drone.get_flight_status_json()  # JSON string with flight status

# Get all telemetry data in JSON format
all_json = drone.get_all_data_json()          # Complete state in JSON
print(all_json)  # Pretty formatted JSON string

# Advanced JSON methods
# Live telemetry for real-time streaming (compact format)
live_json = drone.get_live_telemetry_json()   # Compact JSON for streaming
live_json = drone.get_live_telemetry_json(include_timestamp=False)  # No timestamp

# System status with health indicators
system_json = drone.get_system_status_json()  # Comprehensive system status

# Telemetry streaming for real-time data
stream_json = drone.get_telemetry_stream_json()  # Real-time telemetry stream

# Data summary and statistics
summary_json = drone.get_datastream_summary_json()  # Data stream summary

# Parameters in JSON format
params_json = drone.get_parameters_json()     # All parameters as JSON
```

#### Example JSON Output
```json
{
  "attitude": {
    "roll_deg": 1.2,
    "pitch_deg": -0.8,
    "yaw_deg": 180.5
  },
  "position": {
    "latitude": 21.0285,
    "longitude": 105.8542,
    "altitude_m": 50.3
  },
  "battery": {
    "voltage": 12.6,
    "current": 15.2,
    "remaining_percent": 75
  },
  "flight_status": {
    "mode": "GUIDED",
    "armed": true,
    "connected": true
  }
}
```

#### Command Methods
```python
# Arming/disarming
drone.arm()                           # Arm vehicle
drone.arm(force=True)                 # Force arm (bypass checks)
drone.disarm()                        # Disarm vehicle

# Flight modes
drone.set_mode('GUIDED')              # Set flight mode
drone.set_mode('AUTO')                # Auto mission mode
drone.set_mode('RTL')                 # Return to launch

# Flight commands (requires GUIDED mode and armed)
drone.takeoff(10)                     # Takeoff to 10 meters
drone.land()                          # Land at current position
drone.return_to_launch()              # RTL command
drone.goto_position(21.0285, 105.8542, 50)  # Go to lat, lon, alt
```

#### Parameter Methods
```python
# Get parameter
value = drone.get_parameter('ARMING_CHECK')

# Set parameter  
success = drone.set_parameter('ARMING_CHECK', 1.0)

# Request all parameters
drone.request_all_parameters()
```

#### Mission Methods
```python
# Simple waypoint mission
waypoints = [
    {'lat': 21.0285, 'lon': 105.8542, 'alt': 50},
    {'lat': 21.0295, 'lon': 105.8552, 'alt': 50},
    {'lat': 21.0275, 'lon': 105.8562, 'alt': 50}
]
drone.upload_simple_mission(waypoints)

# Mission control
drone.clear_mission()
drone.request_mission_list()
```

### DroneMAVLinkAPI Class

Low-level MAVLink API for advanced usage with full event system.

#### Event Types
```python
from Call_API import MAVLinkEventType

# Connection events
MAVLinkEventType.CONNECTION_STATE_CHANGED
MAVLinkEventType.HEARTBEAT

# Telemetry events  
MAVLinkEventType.ATTITUDE
MAVLinkEventType.POSITION
MAVLinkEventType.VFR_HUD
MAVLinkEventType.BATTERY_STATUS
MAVLinkEventType.GPS_INFO
MAVLinkEventType.STATUS_TEXT

# Parameter events
MAVLinkEventType.PARAMETER_RECEIVED
MAVLinkEventType.ALL_PARAMETERS_RECEIVED

# Mission events
MAVLinkEventType.MISSION_COUNT
MAVLinkEventType.MISSION_ITEM
MAVLinkEventType.MISSION_CURRENT
MAVLinkEventType.MISSION_ITEM_REACHED
MAVLinkEventType.ALL_MISSION_ITEMS_RECEIVED

# Command events
MAVLinkEventType.COMMAND_ACK
MAVLinkEventType.SYSTEM_TIME
MAVLinkEventType.SCALED_PRESSURE
MAVLinkEventType.SERVO_OUTPUT
MAVLinkEventType.RC_CHANNELS
```

#### Event Handling
```python
api = DroneMAVLinkAPI()

# Add event listener
def my_handler(event):
    print(f"Event: {event.event_type.value}")
    print(f"Data: {event.data}")
    print(f"Timestamp: {event.timestamp}")

api.add_event_listener(MAVLinkEventType.HEARTBEAT, my_handler)

# Remove event listener
api.remove_event_listener(MAVLinkEventType.HEARTBEAT, my_handler)
```

## Connection Strings

The library supports various connection methods:

```python
# Serial connections
drone.connect('/dev/ttyACM0', 115200)        # Linux
drone.connect('COM3', 115200)                # Windows
drone.connect('/dev/tty.usbmodem1', 57600)   # macOS

# Network connections  
drone.connect('udp:127.0.0.1:14550')         # UDP (SITL)
drone.connect('tcp:127.0.0.1:5760')          # TCP
drone.connect('udp:0.0.0.0:14550')           # UDP server mode
```

## Error Handling

```python
from Call_API import DroneController
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

drone = DroneController()

try:
    if not drone.connect('/dev/ttyACM0'):
        print("Failed to connect")
        exit(1)
    
    # Your operations here
    if not drone.arm():
        print("Failed to arm")
        exit(1)
        
except Exception as e:
    print(f"Error: {e}")
finally:
    drone.disconnect()
```

## Common Usage Patterns

### Real-time Monitoring
```python
from Call_API import DroneController, MAVLinkEventType
import time

drone = DroneController()

def on_attitude(event):
    data = event.data
    print(f"Attitude: R={data['roll']:.1f}° P={data['pitch']:.1f}° Y={data['yaw']:.1f}°")

def on_position(event):
    data = event.data
    print(f"Position: {data['lat']:.6f}, {data['lon']:.6f}, Alt={data['alt']:.1f}m")

if drone.connect('/dev/ttyACM0'):
    # Add event listeners for real-time updates
    drone.add_event_listener(MAVLinkEventType.ATTITUDE, on_attitude)
    drone.add_event_listener(MAVLinkEventType.POSITION, on_position)
    
    # Run monitoring loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        drone.disconnect()
```

### Automated Flight Mission
```python
from Call_API import DroneController
import time

drone = DroneController()

if drone.connect('/dev/ttyACM0'):
    print("Connected to drone")
    
    # Wait for GPS fix
    while True:
        gps = drone.get_gps_info()
        if gps['fix_type'] >= 3:  # 3D fix
            print("GPS ready")
            break
        print("Waiting for GPS fix...")
        time.sleep(1)
    
    # Arm and takeoff
    if drone.arm():
        print("Armed successfully")
        
        if drone.takeoff(20):
            print("Takeoff command sent")
            
            # Wait for takeoff
            time.sleep(10)
            
            # Execute mission
            waypoints = [
                {'lat': 21.0285, 'lon': 105.8542, 'alt': 20},
                {'lat': 21.0295, 'lon': 105.8552, 'alt': 20}
            ]
            
            if drone.upload_simple_mission(waypoints):
                print("Mission uploaded")
                drone.set_mode('AUTO')  # Start mission
            
            # Monitor mission progress
            # (Add event listeners for mission events)
            
    drone.disconnect()
```

### Parameter Management
```python
from Call_API import DroneController, MAVLinkEventType
import time

drone = DroneController()

def on_all_parameters(event):
    params = event.data
    print(f"Received {len(params)} parameters")
    
    # Print important parameters
    important = ['ARMING_CHECK', 'BATT_LOW_VOLT', 'RTL_ALT']
    for param in important:
        if param in params:
            print(f"  {param}: {params[param]}")

if drone.connect('/dev/ttyACM0'):
    # Listen for parameter events
    drone.add_event_listener(MAVLinkEventType.ALL_PARAMETERS_RECEIVED, on_all_parameters)
    
    # Request all parameters
    drone.request_all_parameters()
    
    # Wait for parameters
    time.sleep(10)
    
    # Set a parameter
    drone.set_parameter('ARMING_CHECK', 1.0)
    
    drone.disconnect()
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and log back in
   ```

2. **Connection Timeout**
   - Check baud rate (usually 57600 or 115200)
   - Verify connection cable
   - Ensure drone is powered on
   - Check if other software is using the port

3. **No GPS Fix**
   - Move to open area
   - Wait for satellite acquisition
   - Check GPS status with `drone.get_gps_info()`

4. **Arming Failed**
   - Check pre-arm safety checks
   - Use `drone.get_parameter('ARMING_CHECK')` to see requirements
   - Use `drone.arm(force=True)` to bypass checks (unsafe)

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Detailed logs will be shown
drone = DroneController()
```

## Requirements

- Python 3.6+
- pymavlink >= 2.4.37
- Compatible flight controller (ArduPilot, PX4, etc.)

## License

This library is part of the VTOL drone project.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Enable debug logging
3. Review the event logs
4. Consult MAVLink documentation
