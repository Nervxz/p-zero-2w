"""
Preview and Capture Example

This example demonstrates how to start a camera preview,
allow the user to see the preview, and capture an image
when the user presses the Enter key.
"""

from picamera2_restructured import CameraController
import time
import sys

def main():
    # Create camera controller
    camera = CameraController()
    
    # Initialize camera
    print("Initializing camera...")
    camera.initialize()
    
    try:
        # Start a preview window
        print("Starting preview window...")
        camera.preview.start(preview_type='qt', width=800, height=600)
        
        # Wait for auto-exposure to stabilize
        time.sleep(2)
        
        # Prompt user
        print("Preview active. Press Enter to capture an image, or Ctrl+C to quit.")
        
        # Wait for user input
        input()
        
        # Capture a JPEG image
        print("Capturing image...")
        image = camera.capture.capture_image(format='jpeg')
        
        # Save the image to file
        filename = f"preview_capture_{int(time.time())}.jpg"
        with open(filename, 'wb') as f:
            f.write(image)
        
        print(f"Image saved to {filename}")
        
    except KeyboardInterrupt:
        print("\nCapture cancelled by user")
        
    finally:
        # Stop preview
        camera.preview.stop()
        
        # Clean up
        camera.close()
        print("Camera closed")

if __name__ == "__main__":
    main()
