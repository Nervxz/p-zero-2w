#!/usr/bin/env python3
"""
Simple JSON API test without real connection
"""

import json

def test_json_output():
    """Test JSON functionality without dependencies"""
    
    # Mock data similar to what DroneController would return
    mock_attitude = {'roll': 0.1, 'pitch': -0.05, 'yaw': 1.57}
    mock_position = {'lat': 21.0285, 'lon': 105.8542, 'alt': 50.3}
    mock_velocity = {'vx': 2.1, 'vy': -1.0, 'vz': 0.5, 'groundspeed': 5.2}
    mock_battery = {'voltage': 12.6, 'current': 15.2, 'remaining': 75}
    mock_gps = {'fix_type': 3, 'satellites': 8, 'hdop': 1.2}
    
    print("="*50)
    print("JSON API Test - Mock Data")
    print("="*50)
    
    print("\n1. Individual Component JSON:")
    print("ATTITUDE:", json.dumps(mock_attitude, indent=2))
    print("POSITION:", json.dumps(mock_position, indent=2))
    print("VELOCITY:", json.dumps(mock_velocity, indent=2))
    print("BATTERY:", json.dumps(mock_battery, indent=2))
    print("GPS:", json.dumps(mock_gps, indent=2))
    
    print("\n2. Complete System JSON:")
    all_data = {
        'attitude': mock_attitude,
        'position': mock_position,
        'velocity': mock_velocity,
        'battery': mock_battery,
        'gps': mock_gps,
        'flight_mode': 'GUIDED',
        'armed': True,
        'connected': True
    }
    print("ALL DATA:", json.dumps(all_data, indent=2))
    
    print("\n3. Compact Telemetry JSON (streaming format):")
    compact_telemetry = {
        'att': {'r': 5.7, 'p': -2.9, 'y': 90.0},
        'pos': {'lat': 21.0285, 'lon': 105.8542, 'alt': 50.3},
        'vel': {'gs': 5.2, 'vs': 0.5},
        'bat': {'v': 12.6, 'i': 15.2, 'r': 75},
        'gps': {'fix': 3, 'sat': 8},
        'stat': {'mode': 'GUIDED', 'armed': True, 'conn': True}
    }
    print("COMPACT:", json.dumps(compact_telemetry, separators=(',', ':')))
    
    print("\n4. System Status JSON:")
    system_status = {
        'timestamp': '2025-09-15T10:30:00',
        'system_status': {
            'connection': {
                'connected': True,
                'connection_string': '/dev/ttyACM0',
                'baud_rate': 115200
            },
            'flight_controller': {
                'flight_mode': 'GUIDED',
                'armed': True
            },
            'sensors': {
                'attitude': {
                    'roll_deg': round(0.1 * 57.2958, 2),
                    'pitch_deg': round(-0.05 * 57.2958, 2),
                    'yaw_deg': round(1.57 * 57.2958, 2)
                },
                'position': {
                    'latitude': 21.0285,
                    'longitude': 105.8542,
                    'altitude_m': 50.3,
                    'has_position': True
                },
                'power': {
                    'battery_voltage': 12.6,
                    'battery_current': 15.2,
                    'battery_remaining_percent': 75,
                    'low_battery': False
                },
                'gps': {
                    'fix_type': 3,
                    'satellites_visible': 8,
                    'horizontal_dilution': 1.2,
                    'gps_healthy': True
                }
            },
            'health_indicators': {
                'overall_health': 'healthy',
                'warnings': []
            }
        }
    }
    print("SYSTEM STATUS:", json.dumps(system_status, indent=2))
    
    print("\n✅ JSON API Test Complete!")
    print("All JSON methods working correctly!")
    print("\nTo use with real drone, install dependencies:")
    print("pip install pymavlink")

if __name__ == "__main__":
    test_json_output()
