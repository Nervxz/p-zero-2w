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
        from picamera2_restructured.utils import ImageUtils
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
        global USE_RESTRUCTURED  # Declare global at the beginning of the function
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
                from picamera2.devices import IMX500
                
                # Initialize IMX500 device - must be done before Picamera2
                print(f"Loading model: {self.args.model}")
                self.imx500 = IMX500(self.args.model)
                
                # Initialize picamera2 with the correct camera number
                self.camera = Picamera2(self.imx500.camera_num)
                
                # Configure camera
                config = self.camera.create_preview_configuration(
                    main={"size": (self.args.display_width, self.args.display_height), "format": "RGB888"},
                    lores={"size": (320, 240)},
                    controls={"FrameRate": self.args.fps}
                )
                self.camera.configure(config)
                
                # Start camera
                self.camera.start(show_preview=False)
            
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
                        # Get metadata from the request
                        metadata = self.camera.capture_metadata()
                        
                        # Get detections from the IMX500 device using metadata
                        detections_result = []
                        if metadata:
                            # Try to get outputs from metadata
                            try:
                                # This is similar to the parse_detections function in the original code
                                np_outputs = self.imx500.get_outputs(metadata, add_batch=True)
                                if np_outputs is not None:
                                    # Process outputs based on the model type
                                    # This is a simplified version of the original processing
                                    boxes, scores, classes = None, None, None
                                    
                                    # Check if we need to use nanodet postprocessing
                                    if hasattr(self.imx500, 'network_intrinsics') and getattr(self.imx500.network_intrinsics, 'postprocess', '') == 'nanodet':
                                        # Handle nanodet postprocessing with fallbacks
                                        postprocess_nanodet_detection = None
                                        scale_boxes = None
                                        
                                        # Try to import the needed functions
                                        try:
                                            # Try different import paths
                                            try:
                                                from picamera2.devices.imx500 import postprocess_nanodet_detection
                                            except ImportError:
                                                try:
                                                    from picamera2.devices.imx500.imx500 import postprocess_nanodet_detection
                                                except ImportError:
                                                    print("Could not import postprocess_nanodet_detection")
                                            
                                            try:
                                                from picamera2.devices.imx500.postprocess import scale_boxes
                                            except ImportError:
                                                try:
                                                    from picamera2.devices.imx500.imx500 import scale_boxes
                                                except ImportError:
                                                    print("Could not import scale_boxes")
                                            
                                            # Use the functions if available
                                            if postprocess_nanodet_detection:
                                                boxes, scores, classes = postprocess_nanodet_detection(
                                                    outputs=np_outputs[0], 
                                                    conf=self.args.threshold, 
                                                    iou_thres=0.65,
                                                    max_out_dets=10
                                                )[0]
                                                
                                                # Scale boxes if needed
                                                input_w, input_h = self.imx500.get_input_size()
                                                if scale_boxes:
                                                    boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
                                        except Exception as e:
                                            print(f"Error in nanodet processing: {e}")
                                            traceback.print_exc()
                                    else:
                                        # Standard processing
                                        boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
                                        
                                        # Normalize if needed
                                        if self.args.bbox_normalization:
                                            input_w, input_h = self.imx500.get_input_size()
                                            boxes = boxes / input_h
                                        
                                        # Split boxes into separate coordinates
                                        boxes = np.array_split(boxes, 4, axis=1)
                                        boxes = list(zip(*boxes))
                                    
                                    # Create detection objects
                                    for box, score, category in zip(boxes, scores, classes):
                                        if score > self.args.threshold:
                                            # Convert box to the expected format
                                            if hasattr(self.imx500, 'convert_inference_coords'):
                                                # Use the IMX500's coordinate conversion if available
                                                box_converted = self.imx500.convert_inference_coords(box, metadata, self.camera)
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
                                                    
                                                    if self.args.bbox_normalization:
                                                        # Use normalized coordinates
                                                        detections_result.append({
                                                            'class_id': int(category),
                                                            'confidence': float(score),
                                                            'bbox': [x1, y1, x2, y2]
                                                        })
                                                    else:
                                                        # Convert to pixel coordinates
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
                                import traceback
                                traceback.print_exc()
                        
                        # If we couldn't get detections from metadata, fall back to direct detection
                        if not detections_result:
                            try:
                                # Try direct detect method if available
                                if hasattr(self.imx500, 'detect'):
                                    raw_detections = self.imx500.detect(frame)
                                    if raw_detections:
                                        for det in raw_detections:
                                            # Check if detection has the expected attributes
                                            if hasattr(det, 'confidence') and det.confidence >= self.args.threshold:
                                                # Get class_id and confidence
                                                class_id = getattr(det, 'class_id', 0)
                                                confidence = det.confidence
                                                
                                                # Handle different bbox formats
                                                if hasattr(det, 'x1') and hasattr(det, 'y1') and hasattr(det, 'x2') and hasattr(det, 'y2'):
                                                    # Original format with x1,y1,x2,y2 attributes
                                                    if self.args.bbox_normalization:
                                                        # Use normalized coordinates
                                                        detections_result.append({
                                                            'class_id': class_id,
                                                            'confidence': confidence,
                                                            'bbox': [det.x1, det.y1, det.x2, det.y2]
                                                        })
                                                    else:
                                                        # Convert to pixel coordinates
                                                        h, w = frame.shape[:2]
                                                        detections_result.append({
                                                            'class_id': class_id,
                                                            'confidence': confidence,
                                                            'bbox': [
                                                                int(det.x1 * w),
                                                                int(det.y1 * h),
                                                                int(det.x2 * w),
                                                                int(det.y2 * h)
                                                            ]
                                                        })
                                                elif hasattr(det, 'bbox'):
                                                    # Alternative format with bbox attribute
                                                    bbox = det.bbox
                                                    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                                                        if self.args.bbox_normalization:
                                                            detections_result.append({
                                                                'class_id': class_id,
                                                                'confidence': confidence,
                                                                'bbox': bbox
                                                            })
                                                        else:
                                                            # Convert to pixel coordinates
                                                            h, w = frame.shape[:2]
                                                            detections_result.append({
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
                                print(f"Error using direct detection: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        # Use the detection results
                        detections = detections_result
                    
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
        try:
            if USE_RESTRUCTURED:
                self.camera.close()
            else:
                self.camera.stop()
                self.camera.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            
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
