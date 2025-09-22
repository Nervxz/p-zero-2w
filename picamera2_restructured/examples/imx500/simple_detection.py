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
import traceback

# Add both the restructured library and original picamera2 to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import original picamera2 for IMX500 support
original_picamera2_dir = os.path.abspath(os.path.join(root_dir, 'picamera2'))
if original_picamera2_dir not in sys.path:
    sys.path.append(original_picamera2_dir)

# Initialize flag for which implementation to use
USE_RESTRUCTURED = False

try:
    # Try using the restructured library's IMX500 device
    from picamera2_restructured import CameraController
    from picamera2_restructured.devices import DeviceManager
    try:
        from picamera2_restructured.devices.imx500 import IMX500Device
        USE_RESTRUCTURED = True
    except ImportError:
        print("Could not import IMX500Device from restructured library")
except ImportError:
    print("Could not import restructured library modules")

# Always import the original implementation as fallback
try:
    from picamera2 import Picamera2
    try:
        # Different versions of picamera2 might have different import paths
        try:
            from picamera2.devices import IMX500
        except ImportError:
            try:
                from picamera2.devices.imx500 import IMX500
            except ImportError:
                print("Warning: Could not import IMX500 from picamera2")
    except ImportError:
        print("Warning: Could not import device modules from picamera2")
except ImportError:
    print("Warning: Could not import Picamera2")

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
    global USE_RESTRUCTURED  # Declare global at the beginning of the function
    args = parse_args()
    model_path = args.model
    labels_path = args.labels
    fps = args.fps
    threshold = args.threshold
    show_window = args.show_window
    
    print(f"Model path: {model_path}")
    print(f"Labels path: {labels_path}")
    
    # Load labels first since both implementations need them
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
    
    # Initialize camera and IMX500 device based on which implementation is available
    if USE_RESTRUCTURED:
        try:
            print("Using restructured API implementation")
            
            # Initialize device manager
            manager = DeviceManager()
            
            # Get IMX500 device
            imx500 = manager.initialize_device("camera0", "imx500")
            
            if not imx500:
                print("IMX500 device not found using restructured API.")
                print("Trying original picamera2 implementation...")
                # Fall back to original implementation
                USE_RESTRUCTURED = False
            else:
                # Load AI model
                print("Loading model...")
                success = imx500.load_ai_model("efficientdet", model_path)
                if not success:
                    print("Failed to load model with restructured API, trying original implementation...")
                    USE_RESTRUCTURED = False
                else:
                    # Initialize camera
                    print("Initializing camera...")
                    camera = CameraController()
                    camera.initialize()
                    
                    # Start preview
                    camera.preview.start()
                    
                    # Enable AI processing
                    imx500.enable_ai_processing(True)
        except Exception as e:
            print(f"Error with restructured implementation: {e}")
            import traceback
            traceback.print_exc()
            print("Falling back to original implementation...")
            USE_RESTRUCTURED = False
    
    # If restructured implementation failed or was not available, use original picamera2
    if not USE_RESTRUCTURED:
        print("Using original picamera2 implementation")
        
        # Import specific IMX500 implementation from original picamera2
        from picamera2.devices import IMX500
        
        # Initialize IMX500 device - must be done before Picamera2
        print(f"Loading model: {model_path}")
        imx500 = IMX500(model_path)
        
        # Initialize picamera2 with the correct camera number
        camera = Picamera2(imx500.camera_num)
        
        # Configure camera
        config = camera.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            lores={"size": (320, 240)},
            controls={"FrameRate": fps}
        )
        camera.configure(config)
        
        # Start camera
        camera.start(show_preview=False)
    
    print("Detection running. Press Ctrl+C to stop.")
    
    try:
        while True:
            try:
                # Capture frame based on implementation
                if USE_RESTRUCTURED:
                    frame = camera.capture.capture_image(format='array')
                else:
                    frame = camera.capture_array()
                
                # Process frame with IMX500 based on implementation
                if USE_RESTRUCTURED:
                    results = imx500.process_frame(frame)
                    
                    # Filter results by confidence threshold
                    detections = []
                    for detection in results.get('results', []):
                        if detection.get('confidence', 0) >= threshold:
                            detections.append(detection)
                else:
                    # Process frame with original IMX500 API
                    try:
                        # Try to get metadata first (preferred method)
                        metadata = camera.capture_metadata()
                        detections_result = []
                        
                        if metadata and hasattr(imx500, 'get_outputs'):
                            try:
                                # Similar to the object_detection_demo.py approach
                                np_outputs = imx500.get_outputs(metadata, add_batch=True)
                                if np_outputs is not None:
                                    # Process outputs
                                    boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
                                    
                                    # Create detection objects
                                    for box, score, category in zip(boxes, scores, classes):
                                        if score > threshold:
                                            if hasattr(imx500, 'convert_inference_coords'):
                                                # Use the IMX500's coordinate conversion if available
                                                box_converted = imx500.convert_inference_coords(box, metadata, camera)
                                                x, y, w, h = box_converted
                                                detections_result.append({
                                                    'class_id': int(category),
                                                    'confidence': float(score),
                                                    'bbox': [x, y, w, h]
                                                })
                                            else:
                                                # Fallback to simple conversion
                                                if len(box) == 4:
                                                    x1, y1, x2, y2 = box
                                                    h, w = frame.shape[:2]
                                                    detections_result.append({
                                                        'class_id': int(category),
                                                        'confidence': float(score),
                                                        'bbox': [
                                                            int(x1 * w),
                                                            int(y1 * h),
                                                            int(x2 * w),
                                                            int(y2 * h)
                                                        ]
                                                    })
                            except Exception as e:
                                print(f"Error processing metadata: {e}")
                                traceback.print_exc()
                        
                        # If metadata approach didn't work, try direct detection
                        if not detections_result and hasattr(imx500, 'detect'):
                            detections_result = imx500.detect(frame)
                        
                        # Convert to our standard format
                        detections = []
                        if detections_result:
                            # If we already have properly formatted results from metadata
                            if isinstance(detections_result, list) and all(isinstance(d, dict) for d in detections_result):
                                detections = detections_result
                            else:
                                # Process detection objects
                                for det in detections_result:
                                    # Check if detection has the expected attributes
                                    if hasattr(det, 'confidence') and det.confidence >= threshold:
                                        # Get class_id and confidence
                                        class_id = getattr(det, 'class_id', 0)
                                        confidence = det.confidence
                                        
                                        # Handle different bbox formats
                                        if hasattr(det, 'x1') and hasattr(det, 'y1') and hasattr(det, 'x2') and hasattr(det, 'y2'):
                                            # Original format with x1,y1,x2,y2 attributes
                                            detections.append({
                                                'class_id': class_id,
                                                'confidence': confidence,
                                                'bbox': [
                                                    int(det.x1 * frame.shape[1]),
                                                    int(det.y1 * frame.shape[0]),
                                                    int(det.x2 * frame.shape[1]),
                                                    int(det.y2 * frame.shape[0])
                                                ]
                                            })
                                        elif hasattr(det, 'bbox'):
                                            # Alternative format with bbox attribute
                                            bbox = det.bbox
                                            if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                                                # Convert to pixel coordinates if needed
                                                h, w = frame.shape[:2]
                                                detections.append({
                                                    'class_id': class_id,
                                                    'confidence': confidence,
                                                    'bbox': [
                                                        int(bbox[0] * w),
                                                        int(bbox[1] * h),
                                                        int(bbox[2] * w),
                                                        int(bbox[3] * h)
                                                    ]
                                                })
                    except Exception as e:
                        print(f"Error in detection: {e}")
                        traceback.print_exc()
                        detections = []
                
                # Draw detection results
                detections_found = 0
                for detection in detections:
                    confidence = detection.get('confidence', 0)
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
                
            except Exception as e:
                print(f"Frame processing error: {e}")
                traceback.print_exc()
                time.sleep(1/fps)  # Still maintain FPS even during errors
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Clean up based on implementation
        try:
            if USE_RESTRUCTURED:
                camera.preview.stop()
                camera.close()
            else:
                camera.stop()
                camera.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            
        if show_window:
            cv2.destroyAllWindows()
            
        print("Detection stopped.")

if __name__ == "__main__":
    main()
