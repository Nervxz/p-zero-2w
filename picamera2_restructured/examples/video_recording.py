"""
Video Recording Example

This example demonstrates how to record video with the
restructured PiCamera2 library.
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
    
    # Recording duration in seconds
    duration = 10
    
    try:
        # Start a preview window
        print("Starting preview window...")
        camera.preview.start(preview_type='qt', width=800, height=600)
        
        # Wait for auto-exposure to stabilize
        time.sleep(2)
        
        # Start recording
        filename = f"video_{int(time.time())}.mp4"
        print(f"Recording {duration} seconds of video to {filename}...")
        camera.encoding.start_video_recording(filename, quality='high')
        
        # Display countdown
        for remaining in range(duration, 0, -1):
            sys.stdout.write(f"\rRecording: {remaining} seconds remaining...")
            sys.stdout.flush()
            time.sleep(1)
        
        # Stop recording
        print("\nStopping recording...")
        camera.encoding.stop_video_recording()
        print(f"Video saved to {filename}")
        
    except KeyboardInterrupt:
        print("\nRecording cancelled by user")
        camera.encoding.stop_video_recording()
        
    finally:
        # Stop preview
        camera.preview.stop()
        
        # Clean up
        camera.close()
        print("Camera closed")

if __name__ == "__main__":
    main()
