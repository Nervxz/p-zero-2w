"""
Timelapse Example

This example demonstrates how to capture a timelapse sequence
of images using the restructured PiCamera2 library.
"""

from picamera2_restructured import CameraController
import os
import time
import datetime
import sys

def main():
    # Configuration
    interval = 5  # Seconds between captures
    total_captures = 12  # Total number of images to capture
    output_dir = "timelapse_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create camera controller
    camera = CameraController()
    
    # Initialize camera
    print("Initializing camera...")
    camera.initialize()
    
    try:
        # Wait for auto-exposure to stabilize
        print("Waiting for camera to adjust...")
        time.sleep(2)
        
        print(f"Starting timelapse: {total_captures} images at {interval}s intervals")
        print(f"Images will be saved to directory: {output_dir}")
        
        # Capture sequence
        for i in range(total_captures):
            # Display progress
            sys.stdout.write(f"\rCapturing image {i+1}/{total_captures}...")
            sys.stdout.flush()
            
            # Capture image
            image = camera.capture.capture_image(format='jpeg')
            
            # Save the image to file
            filename = os.path.join(output_dir, f"timelapse_{i:04d}.jpg")
            with open(filename, 'wb') as f:
                f.write(image)
            
            # Wait for next interval if not the last capture
            if i < total_captures - 1:
                time.sleep(interval)
        
        print(f"\nTimelapse complete! {total_captures} images saved to {output_dir}")
        
    except KeyboardInterrupt:
        print("\nTimelapse cancelled by user")
        
    finally:
        # Clean up
        camera.close()
        print("Camera closed")

if __name__ == "__main__":
    main()
