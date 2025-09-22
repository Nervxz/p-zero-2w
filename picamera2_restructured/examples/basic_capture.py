"""
Basic Capture Example

This example demonstrates the simplest way to capture an image
using the restructured PiCamera2 library.
"""

from picamera2_restructured import CameraController
import time

def main():
    # Create camera controller
    camera = CameraController()
    
    # Initialize camera
    print("Initializing camera...")
    camera.initialize()
    
    try:
        # Wait for auto-exposure to stabilize
        print("Waiting for camera to adjust...")
        time.sleep(2)
        
        # Capture a JPEG image
        print("Capturing image...")
        image = camera.capture.capture_image(format='jpeg')
        
        # Save the image to file
        filename = f"capture_{int(time.time())}.jpg"
        with open(filename, 'wb') as f:
            f.write(image)
        
        print(f"Image saved to {filename}")
        
    finally:
        # Clean up
        camera.close()
        print("Camera closed")

if __name__ == "__main__":
    main()
