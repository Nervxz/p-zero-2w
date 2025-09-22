"""
Advanced Capture Example

This example demonstrates advanced capture features including:
- Raw capture
- Burst capture
- Capture with image processing
- Custom camera configurations
"""

from picamera2_restructured import CameraController
from picamera2_restructured.utils import ImageUtils
import os
import time
import numpy as np
from PIL import Image

def main():
    # Create output directory
    output_dir = "advanced_captures"
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
        
        # 1. Standard JPEG capture with timestamp
        print("\n1. Capturing JPEG with timestamp...")
        image = camera.capture.capture_image(format='array')
        timestamped = ImageUtils.add_timestamp(image)
        jpeg_data = ImageUtils.array_to_jpeg(timestamped)
        
        with open(os.path.join(output_dir, "timestamped.jpg"), 'wb') as f:
            f.write(jpeg_data)
        
        # 2. RAW capture (if supported)
        print("\n2. Attempting RAW capture...")
        try:
            raw_image = camera.capture.capture_raw()
            # Convert to viewable format and save as PNG
            if raw_image is not None and isinstance(raw_image, np.ndarray):
                img = Image.fromarray(raw_image)
                img.save(os.path.join(output_dir, "raw_capture.png"))
                print("   RAW capture saved as PNG")
            else:
                print("   RAW capture not supported on this device")
        except Exception as e:
            print(f"   RAW capture failed: {e}")
        
        # 3. Burst capture
        print("\n3. Performing burst capture (5 images)...")
        burst_images = []
        for i in range(5):
            sys.stdout.write(f"\r   Capturing image {i+1}/5...")
            sys.stdout.flush()
            image = camera.capture.capture_image(format='jpeg')
            burst_images.append(image)
            time.sleep(0.5)
        
        print("\n   Saving burst images...")
        for i, img in enumerate(burst_images):
            with open(os.path.join(output_dir, f"burst_{i}.jpg"), 'wb') as f:
                f.write(img)
        
        # 4. Image with overlay text
        print("\n4. Capturing image with text overlay...")
        image = camera.capture.capture_image(format='array')
        overlay_text = "PiCamera2 Restructured"
        with_text = ImageUtils.add_overlay_text(image, overlay_text)
        jpeg_data = ImageUtils.array_to_jpeg(with_text)
        
        with open(os.path.join(output_dir, "overlay_text.jpg"), 'wb') as f:
            f.write(jpeg_data)
        
        print(f"\nAll captures completed. Images saved to {output_dir}")
        
    finally:
        # Clean up
        camera.close()
        print("Camera closed")

if __name__ == "__main__":
    import sys  # Import needed for stdout writing
    main()
