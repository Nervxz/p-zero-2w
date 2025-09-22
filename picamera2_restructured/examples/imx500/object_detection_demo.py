#!/usr/bin/env python3

"""
IMX500 Object Detection Demo using the PiCamera2 Restructured API

This script demonstrates object detection using the Sony IMX500 intelligent
vision sensor with embedded AI processing. It adapts the functionality
of the original picamera2 example to work with the restructured API.

Usage:
    python object_detection_demo.py --model /path/to/model.rpk --labels /path/to/labels.txt [options]

Options:
    --model MODEL       Path to the model file (.rpk)
    --labels LABELS     Path to the labels file
    --fps FPS           Frames per second (default: 25)
    --display-width W   Display width (default: 640)
    --display-height H  Display height (default: 480)
    --threshold T       Detection threshold (default: 0.5)
    --bbox-normalization Use normalized bounding box coordinates
    --ignore-dash-labels Ignore labels starting with '-'
"""

import argparse
import cv2
import numpy as np
import time
import os
import sys
from threading import Thread, Lock
import queue

# Add both the restructured library and original picamera2 to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import original picamera2 for IMX500 support
original_picamera2_dir = os.path.abspath(os.path.join(root_dir, 'picamera2'))
if original_picamera2_dir not in sys.path:
    sys.path.append(original_picamera2_dir)

try:
    # Try using the restructured library's IMX500 device
    from picamera2_restructured import CameraController
    from picamera2_restructured.devices import DeviceManager
    from picamera2_restructured.devices.imx500 import IMX500Device
    from picamera2_restructured.utils import ImageUtils
    USE_RESTRUCTURED = True
except ImportError:
    print("Could not import restructured IMX500Device, falling back to original implementation")
    # Fall back to original picamera2 implementation
    from picamera2 import Picamera2
    import picamera2.devices.imx500
    USE_RESTRUCTURED = False

class ObjectDetectionApp:
    """Main application for IMX500 object detection."""
    
    def __init__(self, args):
        """Initialize the application with command line arguments."""
        self.args = args
        self.frame_queue = queue.Queue(maxsize=2)
        self.result_queue = queue.Queue(maxsize=2)
        self.lock = Lock()
        
        # Camera and device setup
        self.camera = None
        self.imx500 = None
        self.labels = []
        
        # Processing state
        self.running = False
        self.latest_frame = None
        self.latest_results = []
        
        # Load labels
        self._load_labels()
    
    def _load_labels(self):
        """Load the class labels from the specified file."""
        try:
            with open(self.args.labels, 'r') as f:
                self.labels = []
                for line in f:
                    if self.args.ignore_dash_labels and line.startswith('-'):
                        continue
                    self.labels.append(line.strip())
            print(f"Loaded {len(self.labels)} labels from {self.args.labels}")
        except Exception as e:
            print(f"Error loading labels: {e}")
            sys.exit(1)
    
    def initialize(self):
        """Initialize camera and IMX500 device."""
        try:
            if USE_RESTRUCTURED:
                # Using restructured API
                # Initialize device manager
                manager = DeviceManager()
                
                # Get IMX500 device
                self.imx500 = manager.initialize_device("camera0", "imx500")
                
                if not self.imx500:
                    print("IMX500 device not found using restructured API.")
                    print("Trying original picamera2 implementation...")
                    # Fall back to original implementation
                    global USE_RESTRUCTURED
                    USE_RESTRUCTURED = False
                else:
                    # Load AI model
                    print(f"Loading model: {self.args.model}")
                    success = self.imx500.load_ai_model("efficientdet", self.args.model)
                    if not success:
                        print(f"Failed to load model: {self.args.model}")
                        sys.exit(1)
                    
                    # Initialize camera
                    print("Initializing camera...")
                    self.camera = CameraController()
                    success = self.camera.initialize()
                    if not success:
                        print("Failed to initialize camera")
                        sys.exit(1)
                    
                    # Configure camera
                    self.camera.configure({
                        'main': {'size': (self.args.display_width, self.args.display_height)},
                        'lores': {'size': (320, 240)},
                        'controls': {'FrameRate': self.args.fps}
                    })
                    
                    # Enable AI processing
                    self.imx500.enable_ai_processing(True)
                    
            if not USE_RESTRUCTURED:
                # Using original picamera2 implementation
                print("Using original picamera2 implementation")
                
                # Import specific IMX500 implementation from original picamera2
                from picamera2.devices.imx500.imx500 import IMX500, IMXDetection
                
                # Initialize picamera2
                self.camera = Picamera2()
                
                # Configure camera
                config = self.camera.create_preview_configuration(
                    main={"size": (self.args.display_width, self.args.display_height)},
                    lores={"size": (320, 240)},
                    controls={"FrameRate": self.args.fps}
                )
                self.camera.configure(config)
                
                # Start camera
                self.camera.start()
                
                # Initialize IMX500 device
                self.imx500 = IMX500()
                
                # Load model
                print(f"Loading model: {self.args.model}")
                self.imx500.load_model(self.args.model)
            
            print("Initialization complete")
            return True
            
        except Exception as e:
            print(f"Initialization error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def capture_thread(self):
        """Thread for capturing frames from the camera."""
        try:
            while self.running:
                # Capture frame - handle both implementations
                if USE_RESTRUCTURED:
                    frame = self.camera.capture.capture_image(format='array')
                else:
                    # Using original picamera2
                    frame = self.camera.capture_array()
                
                # Update latest frame with lock
                with self.lock:
                    self.latest_frame = frame.copy()
                
                # Put in queue for processing (non-blocking)
                try:
                    self.frame_queue.put(frame, block=False)
                except queue.Full:
                    pass  # Skip frame if queue is full
                
                # Maintain FPS
                time.sleep(1.0 / self.args.fps)
        except Exception as e:
            print(f"Capture thread error: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
    
    def processing_thread(self):
        """Thread for processing frames with IMX500."""
        try:
            while self.running:
                try:
                    # Get frame from queue with timeout
                    frame = self.frame_queue.get(timeout=1.0)
                    
                    if USE_RESTRUCTURED:
                        # Process frame with restructured IMX500 API
                        results = self.imx500.process_frame(frame)
                        
                        # Filter results by confidence threshold
                        detections = []
                        for detection in results.get('results', []):
                            if detection.get('confidence', 0) >= self.args.threshold:
                                detections.append(detection)
                    else:
                        # Process frame with original IMX500 API
                        # First, detect the objects
                        detections_result = self.imx500.detect(frame)
                        
                        # Convert to our standard format
                        detections = []
                        if detections_result:
                            for det in detections_result:
                                if det.confidence >= self.args.threshold:
                                    if self.args.bbox_normalization:
                                        # Use normalized coordinates
                                        detections.append({
                                            'class_id': det.class_id,
                                            'confidence': det.confidence,
                                            'bbox': [det.x1, det.y1, det.x2, det.y2]
                                        })
                                    else:
                                        # Convert to pixel coordinates
                                        h, w = frame.shape[:2]
                                        detections.append({
                                            'class_id': det.class_id,
                                            'confidence': det.confidence,
                                            'bbox': [
                                                int(det.x1 * w),
                                                int(det.y1 * h),
                                                int(det.x2 * w),
                                                int(det.y2 * h)
                                            ]
                                        })
                    
                    # Update latest results with lock
                    with self.lock:
                        self.latest_results = detections
                    
                    # Put in result queue (non-blocking)
                    try:
                        self.result_queue.put((frame, detections), block=False)
                    except queue.Full:
                        pass
                    
                except queue.Empty:
                    pass  # No frames available
                    
        except Exception as e:
            print(f"Processing thread error: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
    
    def display_thread(self):
        """Thread for displaying the processed frames with detection results."""
        try:
            while self.running:
                try:
                    # Get processed frame and results
                    frame, detections = self.result_queue.get(timeout=1.0)
                    
                    # Draw detection results
                    display_frame = frame.copy()
                    self._draw_detections(display_frame, detections)
                    
                    # Show frame
                    cv2.imshow("IMX500 Object Detection", display_frame)
                    
                    # Exit if 'q' pressed
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.running = False
                    
                except queue.Empty:
                    # If no new frame, use the latest frame and results
                    with self.lock:
                        if self.latest_frame is not None:
                            display_frame = self.latest_frame.copy()
                            self._draw_detections(display_frame, self.latest_results)
                            cv2.imshow("IMX500 Object Detection", display_frame)
                            
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                self.running = False
        
        except Exception as e:
            print(f"Display thread error: {e}")
            self.running = False
    
    def _draw_detections(self, frame, detections):
        """Draw detection boxes and labels on the frame."""
        h, w = frame.shape[:2]
        
        for detection in detections:
            # Get detection info
            class_id = detection.get('class_id', 0)
            confidence = detection.get('confidence', 0)
            bbox = detection.get('bbox', [0, 0, 0, 0])  # [x1, y1, x2, y2]
            
            # Convert normalized coordinates if needed
            if self.args.bbox_normalization:
                x1, y1, x2, y2 = bbox
            else:
                x1 = int(bbox[0] * w)
                y1 = int(bbox[1] * h)
                x2 = int(bbox[2] * w)
                y2 = int(bbox[3] * h)
            
            # Ensure coordinates are within frame
            x1 = max(0, min(w-1, x1))
            y1 = max(0, min(h-1, y1))
            x2 = max(0, min(w-1, x2))
            y2 = max(0, min(h-1, y2))
            
            # Get label
            label = self.labels[class_id] if class_id < len(self.labels) else f"Class {class_id}"
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label with confidence
            label_text = f"{label}: {confidence:.2f}"
            label_size, baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            y1 = max(y1, label_size[1])
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 5), (x1 + label_size[0], y1 + baseline - 5), (0, 0, 0), -1)
            cv2.putText(frame, label_text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def run(self):
        """Run the object detection application."""
        if not self.initialize():
            return
        
        self.running = True
        
        # Start camera
        self.camera.start()
        
        # Create and start threads
        threads = []
        threads.append(Thread(target=self.capture_thread, daemon=True))
        threads.append(Thread(target=self.processing_thread, daemon=True))
        threads.append(Thread(target=self.display_thread, daemon=True))
        
        for thread in threads:
            thread.start()
        
        try:
            # Wait for threads or user interruption
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping application...")
            self.running = False
        
        # Wait for threads to finish
        for thread in threads:
            thread.join(timeout=1.0)
        
        # Clean up
        cv2.destroyAllWindows()
        
        # Close camera based on implementation
        if USE_RESTRUCTURED:
            self.camera.close()
        else:
            self.camera.stop()
            self.camera.close()
            
        print("Application stopped")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="IMX500 Object Detection Demo")
    parser.add_argument("--model", required=True, help="Path to the model file (.rpk)")
    parser.add_argument("--labels", required=True, help="Path to the labels file")
    parser.add_argument("--fps", type=int, default=25, help="Frames per second (default: 25)")
    parser.add_argument("--display-width", type=int, default=640, help="Display width (default: 640)")
    parser.add_argument("--display-height", type=int, default=480, help="Display height (default: 480)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Detection threshold (default: 0.5)")
    parser.add_argument("--bbox-normalization", action="store_true", help="Use normalized bounding box coordinates")
    parser.add_argument("--ignore-dash-labels", action="store_true", help="Ignore labels starting with '-'")
    
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_arguments()
    app = ObjectDetectionApp(args)
    app.run()

if __name__ == "__main__":
    main()
