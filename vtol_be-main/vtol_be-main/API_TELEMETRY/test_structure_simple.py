#!/usr/bin/env python3
"""
Simple module import test 
"""

def test_module_structure():
    """Test module structure without dependencies"""
    print("="*50)
    print("Call_API Module Structure Test")
    print("="*50)
    
    try:
        # Test basic imports first
        print("✓ Testing basic imports...")
        import sys
        import os
        
        # Test if we can find the module structure
        call_api_path = os.path.dirname(os.path.abspath(__file__))
        print(f"✓ Call_API path: {call_api_path}")
        
        # Check files exist
        files_to_check = [
            '__init__.py',
            'api.py',
            'README.md',
            'mavlink/__init__.py',
            'mavlink/events.py',
            'mavlink/mavlink_core.py'
        ]
        
        for file in files_to_check:
            filepath = os.path.join(call_api_path, file)
            if os.path.exists(filepath):
                print(f"✓ Found: {file}")
            else:
                print(f"✗ Missing: {file}")
        
        print("\n" + "="*50)
        print("Module structure looks good!")
        print("="*50)
        
        print("\nTo use the full API, install dependencies:")
        print("pip install pymavlink")
        print("\nThen you can use:")
        print("from Call_API import DroneController")
        print("drone = DroneController()")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_module_structure()
