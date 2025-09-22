#!/usr/bin/env python3
"""
Test script to demonstrate JSON API functionality
This script tests all the JSON methods of the DroneController class
"""

import json
import time
import sys
import os

# Add the parent directory to Python path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import from the Call_API package
from Call_API import DroneController

def pretty_print_json(json_str: str, title: str):
    """Helper to pretty print JSON with title"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    try:
        data = json.loads(json_str)
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print("Invalid JSON:", json_str)

def test_json_methods():
    """Test all JSON methods"""
    
    # Create drone controller
    drone = DroneController()
    
    print("Testing JSON API Methods")
    print("=" * 60)
    
    # Test all JSON methods even without connection
    print("\n1. Testing Basic JSON Data Methods")
    
    # Individual component JSON methods
    pretty_print_json(drone.get_attitude_json(), "ATTITUDE JSON")
    pretty_print_json(drone.get_position_json(), "POSITION JSON") 
    pretty_print_json(drone.get_velocity_json(), "VELOCITY JSON")
    pretty_print_json(drone.get_battery_status_json(), "BATTERY STATUS JSON")
    pretty_print_json(drone.get_gps_info_json(), "GPS INFO JSON")
    pretty_print_json(drone.get_flight_status_json(), "FLIGHT STATUS JSON")
    
    print("\n2. Testing Comprehensive JSON Methods")
    
    # All data in JSON
    pretty_print_json(drone.get_all_data_json(), "ALL DATA JSON")
    
    # System status JSON
    pretty_print_json(drone.get_system_status_json(), "SYSTEM STATUS JSON")
    
    # Live telemetry JSON (compact format)
    pretty_print_json(drone.get_live_telemetry_json(), "LIVE TELEMETRY JSON (with timestamp)")
    pretty_print_json(drone.get_live_telemetry_json(include_timestamp=False), "LIVE TELEMETRY JSON (no timestamp)")
    
    # Telemetry stream JSON
    pretty_print_json(drone.get_telemetry_stream_json(), "TELEMETRY STREAM JSON")
    
    # Datastream summary JSON
    pretty_print_json(drone.get_datastream_summary_json(), "DATASTREAM SUMMARY JSON")
    
    # Parameters JSON
    pretty_print_json(drone.get_parameters_json(), "PARAMETERS JSON")
    
    print("\n3. Testing with Connection (if available)")
    
    # Try to connect to a common connection string
    connection_strings = [
        '/dev/ttyACM0',
        'COM3', 
        'udp:127.0.0.1:14550',
        'tcp:127.0.0.1:5760'
    ]
    
    connected = False
    for conn_str in connection_strings:
        print(f"\nTrying to connect to: {conn_str}")
        try:
            if drone.connect(conn_str, timeout=5):
                print(f"✓ Connected to {conn_str}")
                connected = True
                break
            else:
                print(f"✗ Failed to connect to {conn_str}")
        except Exception as e:
            print(f"✗ Connection error to {conn_str}: {e}")
    
    if connected:
        print("\n4. Testing with Live Connection")
        
        # Wait a moment for data
        time.sleep(2)
        
        # Test JSON methods with real data
        pretty_print_json(drone.get_all_data_json(), "LIVE ALL DATA JSON")
        pretty_print_json(drone.get_system_status_json(), "LIVE SYSTEM STATUS JSON")
        pretty_print_json(drone.get_live_telemetry_json(), "LIVE TELEMETRY JSON")
        
        # Test streaming data
        print("\n5. Testing Real-time JSON Streaming")
        for i in range(5):
            live_data = drone.get_live_telemetry_json(include_timestamp=True)
            print(f"Stream {i+1}: {live_data}")
            time.sleep(1)
        
        drone.disconnect()
        print("\n✓ Disconnected")
    else:
        print("\n⚠ No connection available - testing with mock data only")
    
    print("\n" + "="*60)
    print("JSON API Test Complete!")
    print("="*60)

if __name__ == "__main__":
    try:
        test_json_methods()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()
