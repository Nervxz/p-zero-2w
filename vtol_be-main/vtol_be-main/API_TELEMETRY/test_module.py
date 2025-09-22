#!/usr/bin/env python3
"""
Simple test script to verify the Call_API module works correctly
Run this to test the module installation and basic functionality
"""

def test_imports():
    """Test if all imports work correctly"""
    try:
        print("Testing module imports...")
        
        # Test main module import
        from Call_API import DroneController, DroneMAVLinkAPI, MAVLinkEventType
        print("✅ Main imports successful")
        
        # Test individual components
        from Call_API.mavlink import DroneMAVLinkAPI as CoreAPI
        from Call_API.mavlink import MAVLinkEventType as EventType
        from Call_API.mavlink import MAVLinkConnectionState
        print("✅ Core component imports successful")
        
        # Test handlers import
        from Call_API.mavlink.handlers import DataStreamHandler
        from Call_API.mavlink.handlers import ParameterHandler
        from Call_API.mavlink.handlers import CommandHandler
        from Call_API.mavlink.handlers import MissionHandler
        print("✅ Handler imports successful")
        
        print("\n🎉 All imports successful! Module is ready to use.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without requiring hardware"""
    try:
        print("\nTesting basic functionality...")
        
        from Call_API import DroneController, MAVLinkEventType
        
        # Test controller creation
        drone = DroneController()
        print("✅ DroneController created successfully")
        
        # Test event types enumeration
        event_count = len([attr for attr in dir(MAVLinkEventType) if not attr.startswith('_')])
        print(f"✅ Found {event_count} event types")
        
        # Test some key event types exist
        key_events = ['HEARTBEAT', 'ATTITUDE', 'POSITION', 'BATTERY_STATUS']
        for event in key_events:
            if hasattr(MAVLinkEventType, event):
                print(f"✅ Event type {event} exists")
            else:
                print(f"❌ Missing event type {event}")
                return False
        
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        return False

def show_usage_example():
    """Show a usage example"""
    print("\n" + "="*60)
    print("USAGE EXAMPLE")
    print("="*60)
    
    example_code = '''
# Example 1: Simple drone monitoring
from Call_API import DroneController

drone = DroneController()
if drone.connect('/dev/ttyACM0', 115200):
    attitude = drone.get_attitude()
    position = drone.get_position()
    battery = drone.get_battery_status()
    
    print(f"Roll: {attitude['roll']:.1f}°")
    print(f"Position: {position['lat']:.6f}, {position['lon']:.6f}")
    print(f"Battery: {battery['voltage']:.1f}V")
    
    drone.disconnect()

# Example 2: Event-driven monitoring  
from Call_API import DroneMAVLinkAPI, MAVLinkEventType

api = DroneMAVLinkAPI()

def on_attitude(event):
    data = event.data
    print(f"Attitude: R={data['roll']:.1f}° P={data['pitch']:.1f}°")

api.add_event_listener(MAVLinkEventType.ATTITUDE, on_attitude)

if api.connect('/dev/ttyACM0', 115200):
    api.configure_standard_streams()
    # Event handlers will be called automatically
    api.dispose()

# Example 3: Context manager
from Call_API import DroneController

with DroneController() as drone:
    if drone.connect('/dev/ttyACM0'):
        data = drone.get_all_data()
        print(f"Flight mode: {data['flight_mode']}")
        # Auto-disconnect when exiting context
'''
    
    print(example_code)

def main():
    """Main test function"""
    print("Call_API Module Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Module test FAILED - Import issues")
        return 1
    
    # Test basic functionality  
    if not test_basic_functionality():
        print("\n❌ Module test FAILED - Functionality issues")
        return 1
    
    # Show usage examples
    show_usage_example()
    
    print("\n" + "="*60)
    print("🎉 SUCCESS: Call_API module is properly installed and ready to use!")
    print("="*60)
    print("\nNext steps:")
    print("1. Connect your drone to the computer")
    print("2. Use the examples in README.md")
    print("3. Check connection string (usually /dev/ttyACM0 or COM port)")
    print("4. Enable debug logging if needed: logging.basicConfig(level=logging.DEBUG)")
    
    return 0

if __name__ == "__main__":
    exit(main())
