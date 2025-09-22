#!/usr/bin/env python3
"""
Simple structure test for Call_API module - no external dependencies required
"""

import os
import sys

def test_file_structure():
    """Test if all required files exist"""
    print("Testing Call_API module structure...")
    
    # Get Call_API directory path
    call_api_dir = os.path.dirname(os.path.abspath(__file__))
    
    required_files = [
        '__init__.py',
        'api.py', 
        'README.md',
        'requirements.txt',
        'mavlink/__init__.py',
        'mavlink/events.py',
        'mavlink/mavlink_core.py',
        'mavlink/handlers/__init__.py',
        'mavlink/handlers/data_stream_handler.py',
        'mavlink/handlers/parameter_handler.py',
        'mavlink/handlers/command_handler.py',
        'mavlink/handlers/mission_handler.py'
    ]
    
    print(f"Call_API directory: {call_api_dir}")
    
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(call_api_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            all_exist = False
    
    return all_exist

def test_basic_imports():
    """Test basic Python imports without pymavlink"""
    print("\nTesting basic imports...")
    
    try:
        # Add Call_API parent directory to path
        call_api_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, call_api_parent)
        
        # Test individual file imports (bypass pymavlink requirement)
        import Call_API
        print("✅ Call_API package imported")
        
        # Check if __all__ is defined
        if hasattr(Call_API, '__all__'):
            print(f"✅ __all__ defined with {len(Call_API.__all__)} exports")
            for item in Call_API.__all__:
                print(f"   - {item}")
        
        return True
        
    except ImportError as e:
        # This is expected due to missing pymavlink
        if 'pymavlink' in str(e).lower():
            print("⚠️  ImportError due to missing pymavlink (expected)")
            print("   Install with: pip install pymavlink")
            return True  # This is OK, just missing dependency
        else:
            print(f"❌ Unexpected import error: {e}")
            return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def show_final_structure():
    """Show the final clean structure"""
    print("\n" + "="*50)
    print("FINAL CALL_API MODULE STRUCTURE")
    print("="*50)
    
    structure = """
Call_API/
├── __init__.py          # Main module exports
├── api.py              # High-level DroneController API
├── requirements.txt    # Dependencies (pymavlink, etc.)
├── README.md          # Complete API documentation
├── test_module.py     # Module test script
└── mavlink/           # Core MAVLink implementation
    ├── __init__.py    # Core exports
    ├── events.py      # Event type definitions
    ├── mavlink_core.py # Main DroneMAVLinkAPI class
    └── handlers/      # Modular handlers
        ├── __init__.py
        ├── data_stream_handler.py
        ├── parameter_handler.py
        ├── command_handler.py
        └── mission_handler.py
"""
    print(structure)

def show_usage_summary():
    """Show usage summary"""
    print("="*50)
    print("USAGE SUMMARY")
    print("="*50)
    
    usage = """
# Installation:
cd vtol_embedded/
pip install -r Call_API/requirements.txt

# Simple usage:
from Call_API import DroneController

drone = DroneController()
if drone.connect('/dev/ttyACM0', 115200):
    attitude = drone.get_attitude()
    print(f"Roll: {attitude['roll']:.1f}°")
    drone.disconnect()

# Advanced usage:
from Call_API import DroneMAVLinkAPI, MAVLinkEventType

api = DroneMAVLinkAPI()
api.add_event_listener(MAVLinkEventType.ATTITUDE, handler)
api.connect('/dev/ttyACM0', 115200)

# Context manager:
with DroneController() as drone:
    if drone.connect('/dev/ttyACM0'):
        data = drone.get_all_data()
"""
    print(usage)

def main():
    """Main test function"""
    print("Call_API Module Structure Test")
    print("=" * 40)
    
    # Test file structure
    if not test_file_structure():
        print("\n❌ FAILED: Missing required files")
        return 1
    
    # Test basic imports
    if not test_basic_imports():
        print("\n❌ FAILED: Import issues")
        return 1
    
    # Show structure and usage
    show_final_structure()
    show_usage_summary()
    
    print("="*50)
    print("🎉 SUCCESS: Call_API module structure is correct!")
    print("="*50)
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Test with hardware: python test_module.py")
    print("3. See README.md for complete documentation")
    print("4. Use from other modules: from Call_API import DroneController")
    
    return 0

if __name__ == "__main__":
    exit(main())
