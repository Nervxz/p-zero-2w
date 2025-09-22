"""
DroneMAVLinkAPI - Comprehensive Python MAVLink Library for Drone Communication

This module provides a complete, event-driven interface for communicating with
MAVLink-compatible flight controllers and drones.

Key Features:
- Event-driven architecture with 20+ event types
- Comprehensive parameter management
- Mission planning and execution
- Real-time telemetry data streaming
- Flight command interface
- Connection management with auto-reconnect
- Thread-safe operations

Usage:
    from Call_API import DroneMAVLinkAPI, MAVLinkEventType
    
    # Create API instance
    api = DroneMAVLinkAPI()
    
    # Add event listener
    def on_heartbeat(event):
        print(f"Heartbeat: {event.data}")
    
    api.add_event_listener(MAVLinkEventType.HEARTBEAT, on_heartbeat)
    
    # Connect to drone
    if api.connect('/dev/ttyACM0', 115200):
        api.configure_standard_streams()
        # Your code here...
    
    # Clean up
    api.dispose()

Author: VTOL Drone Team
Version: 2.0.0
"""

from .mavlink import (
    DroneMAVLinkAPI,
    MAVLinkEventType,
    MAVLinkEvent,
    MAVLinkConnectionState
)

from .api import DroneController

__version__ = "0.0.1"
__author__ = "Rustech developer"

__all__ = [
    'DroneMAVLinkAPI',
    'DroneController',
    'MAVLinkEventType', 
    'MAVLinkEvent',
    'MAVLinkConnectionState'
]
