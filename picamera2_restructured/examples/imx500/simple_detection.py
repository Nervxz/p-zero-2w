#!/usr/bin/env python3

"""
Simple IMX500 Object Detection using PiCamera2 Restructured

This script provides a straightforward implementation of object detection
using the Sony IMX500 intelligent vision sensor with the restructured API.

Usage:
    python simple_detection.py --model /path/to/model.rpk --labels /path/to/labels.txt
"""

import argparse
import cv2
import numpy as np
import time
import os
import sys

# Ensure picamera2_restructured is in the path
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from picamera2_restructured import CameraController
from picamera2_restructured.devices import DeviceManager
from picamera2_restructured.devices.imx500 import IMX500Device

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Simple IMX500 Object Detection')
    parser.add_argument('--model', required=True, help='Path to the model file (.rpk)')
    parser.add_argument('--labels', required=True, help='Path to the labels file')
    parser.add_argument('--fps', type=int, default=25, help='Frames per second (default: 25)')
    parser.add_argument('--threshold', type=float, default=0.5, help='Detection threshold (default: 0.5)')
    parser.add_argument('--show-window', action='store_true', help='Show detection window (default: False)')
    parser.add_argument('--ignore-dash-labels', action='store_true', help='Ignore labels starting with "-"')
    return parser.parse_args()

def main():
    # Parse arguments
    args = parse_args()
    model_path = args.model
    labels_path = args.labels
    fps = args.fps
    threshold = args.threshold
    show_window = args.show_window
    
    print(f"Model path: {model_path}")
    print(f"Labels path: {labels_path}")
    
    # Initialize device manager
    manager = DeviceManager()
    
    # Get IMX500 device
    imx500 = manager.initialize_device("camera0", "imx500")
    
    if not imx500:
        print("IMX500 device not found")
        exit(1)
    
    # Load AI model
    print("Loading model...")
    imx500.load_ai_model("efficientdet", model_path)
    
    # Load labels
    print("Loading labels...")
    try:
        with open(labels_path, 'r') as f:
            if args.ignore_dash_labels:
                labels = [line.strip() for line in f if not line.startswith('-')]
            else:
                labels = [line.strip() for line in f]
        print(f"Loaded {len(labels)} labels")
    except Exception as e:
        print(f"Error loading labels: {e}")
        exit(1)
    
    # Initialize camera
    print("Initializing camera...")
    camera = CameraController()
    camera.initialize()
    
    # Start preview
    camera.preview.start()
    
    # Enable AI processing
    imx500.enable_ai_processing(True)
    
    print("Detection running. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Capture frame
            frame = camera.capture.capture_image(format='array')
            
            # Process frame with IMX500
            results = imx500.process_frame(frame)
            
            # Draw detection results
            detections_found = 0
            for detection in results.get('results', []):
                confidence = detection.get('confidence', 0)
                
                # Skip if below threshold
                if confidence < threshold:
                    continue
                    
                class_id = detection.get('class_id', 0)
                label = labels[class_id] if class_id < len(labels) else str(class_id)
                bbox = detection.get('bbox', [0, 0, 0, 0])  # [x1, y1, x2, y2]
                
                # Draw bounding box
                cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
                cv2.putText(frame, f"{label}: {confidence:.2f}", (int(bbox[0]), int(bbox[1])-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                detections_found += 1
            
            # Print detection count (optional)
            if detections_found > 0:
                print(f"Found {detections_found} objects")
            
            # Display the frame if requested
            if show_window:
                cv2.imshow("IMX500 Object Detection", frame)
                
                # Press 'q' to exit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
            # Maintain FPS
            time.sleep(1/fps)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Clean up
        camera.preview.stop()
        camera.close()
        if show_window:
            cv2.destroyAllWindows()
        print("Detection stopped.")

if __name__ == "__main__":
    main()
