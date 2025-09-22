#!/usr/bin/env python3

"""
Optimized IMX500 Object Detection Demo using the PiCamera2 Restructured API

This script demonstrates object detection using the Sony IMX500 intelligent
vision sensor with embedded AI processing. It is optimized for performance
using caching, parallel processing, and memory optimizations.

Usage:
    python optimized_detection_demo.py --model /path/to/model.rpk --labels /path/to/labels.txt [options]

Options:
    --model MODEL       Path to the model file (.rpk)
    --labels LABELS     Path to the labels file
    --fps FPS           Frames per second (default: 25)
    --display-width W   Display width (default: 640)
    --display-height H  Display height (default: 480)
    --threshold T       Detection threshold (default: 0.5)
    --bbox-normalization Use normalized bounding box coordinates
    --ignore-dash-labels Ignore labels starting with '-'
    --workers N         Number of worker threads (default: auto)
    --profile           Enable performance profiling
    --optimize-memory   Enable memory optimizations
"""

import argparse
import cv2
import numpy as np
import time
import os
import sys
from threading import Thread, Event, RLock
import queue
import traceback
from functools import lru_cache
import multiprocessing

# Add both the restructured library and original picamera2 to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import from restructured library
try:
    from picamera2_restructured import CameraController
    from picamera2_restructured.devices import DeviceManager
    from picamera2_restructured.utils import (
        # Cache utilities
        memoize, get_cached_label, 
        # Memory utilities
        optimize_memory, reduce_memory_usage, memory_pool,
        # Parallel utilities
        ThreadPool, WorkerPool,
        # Profiling utilities
        Timer, timing_decorator, performance_tracker,
        # Image optimization utilities
        optimize_image, fast_resize, fast_convert_color, 
        optimize_bounding_boxes, draw_optimized_boxes
    )
    USE_RESTRUCTURED = True
except ImportError:
    print("Could not import restructured library modules")
    USE_RESTRUCTURED = False

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

# Global performance tracking
ENABLE_PROFILING = False

class OptimizedDetectionApp:
    """
    Optimized application for IMX500 object detection.
    
    Uses performance optimizations like caching, parallel processing,
    and memory optimizations for better performance.
    """
    
    def __init__(self, args):
        """Initialize the application with command line arguments."""
        self.args = args
        
        # Enable profiling if requested
        global ENABLE_PROFILING
        ENABLE_PROFILING = args.profile
        
        # Set up threading and synchronization
        self.frame_queue = queue.Queue(maxsize=3)  # Limit queue size for memory efficiency
        self.result_queue = queue.Queue(maxsize=3)
        self.lock = RLock()
        self.stop_event = Event()
        
        # Set up worker pool
        self.num_workers = args.workers or max(1, multiprocessing.cpu_count() - 1)
        self.worker_pool = ThreadPool(num_threads=self.num_workers)
        
        # Camera and device setup
        self.camera = None
        self.imx500 = None
        self.labels = []
        
        # Processing state
        self.latest_frame = None
        self.latest_results = []
        
        # Load labels
        self._load_labels()
    
    @timing_decorator(verbose=False)
    def _load_labels(self):
        """Load the class labels from the specified file."""
        try:
            with open(self.args.labels, 'r') as f:
                self.labels = []
                for line in f:
                    if self.args.ignore_dash_labels and line.startswith('-'):
                        continue
                    self.labels.append(line.strip())
            
            # Convert to tuple for caching
            self.labels = tuple(self.labels)
            print(f"Loaded {len(self.labels)} labels from {self.args.labels}")
        except Exception as e:
            print(f"Error loading labels: {e}")
            sys.exit(1)
    
    @timing_decorator(verbose=False)
    def initialize(self):
        """Initialize camera and IMX500 device."""
        global USE_RESTRUCTURED
        
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
                
                # Show network firmware progress bar if available
                if hasattr(self.imx500, 'show_network_fw_progress_bar'):
                    print("Showing network firmware upload progress...")
                    self.imx500.show_network_fw_progress_bar()
                
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
            traceback.print_exc()
            return False
    
    @timing_decorator(verbose=False)
    def capture_thread(self):
        """Thread for capturing frames from the camera."""
        last_capture_time = 0
        frame_interval = 1.0 / self.args.fps
        
        try:
            while not self.stop_event.is_set():
                current_time = time.time()
                
                # Maintain consistent frame rate
                if current_time - last_capture_time < frame_interval:
                    # Short sleep to avoid busy waiting
                    time.sleep(0.001)
                    continue
                
                try:
                    # Capture frame - handle both implementations
                    if USE_RESTRUCTURED:
                        frame = self.camera.capture.capture_image(format='array')
                    else:
                        # Using original picamera2
                        frame = self.camera.capture_array()
                    
                    # Optimize image if requested
                    if self.args.optimize_memory:
                        frame = optimize_image(frame)
                    
                    # Update latest frame with lock
                    with self.lock:
                        # Store reference without copying
                        self.latest_frame = frame
                    
                    # Put in queue for processing (non-blocking)
                    if not self.frame_queue.full():
                        self.frame_queue.put(frame, block=False)
                    
                    # Update timing
                    last_capture_time = time.time()
                    if ENABLE_PROFILING:
                        performance_tracker.record('capture_fps', 1.0 / (last_capture_time - current_time))
                    
                except Exception as e:
                    print(f"Capture error: {e}")
                    traceback.print_exc()
                    time.sleep(0.1)  # Avoid rapid error loops
                
        except Exception as e:
            print(f"Capture thread error: {e}")
            traceback.print_exc()
            self.stop_event.set()
    
    @timing_decorator(verbose=False)
    def process_frame(self, frame):
        """
        Process a single frame for object detection.
        
        Args:
            frame: Input frame
            
        Returns:
            List of detection results
        """
        try:
            if USE_RESTRUCTURED:
                # Process frame with restructured IMX500 API
                results = self.imx500.process_frame(frame)
                
                # Filter results by confidence threshold
                detections = []
                for detection in results.get('results', []):
                    if detection.get('confidence', 0) >= self.args.threshold:
                        detections.append(detection)
                
                return detections
            else:
                # Process frame with original IMX500 API
                try:
                    # Try to get metadata first (preferred method)
                    metadata = self.camera.capture_metadata()
                    detections_result = []
                    
                    if metadata and hasattr(self.imx500, 'get_outputs'):
                        try:
                            # Similar to the parse_detections function in the original code
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
                            traceback.print_exc()
                    
                    # If metadata approach didn't work, try direct detection
                    if not detections_result and hasattr(self.imx500, 'detect'):
                        detections_result = self.imx500.detect(frame)
                    
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
                                if hasattr(det, 'confidence') and det.confidence >= self.args.threshold:
                                    # Get class_id and confidence
                                    class_id = getattr(det, 'class_id', 0)
                                    confidence = det.confidence
                                    
                                    # Handle different bbox formats
                                    if hasattr(det, 'x1') and hasattr(det, 'y1') and hasattr(det, 'x2') and hasattr(det, 'y2'):
                                        # Original format with x1,y1,x2,y2 attributes
                                        if self.args.bbox_normalization:
                                            # Use normalized coordinates
                                            detections.append({
                                                'class_id': class_id,
                                                'confidence': confidence,
                                                'bbox': [det.x1, det.y1, det.x2, det.y2]
                                            })
                                        else:
                                            # Convert to pixel coordinates
                                            h, w = frame.shape[:2]
                                            detections.append({
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
                                                detections.append({
                                                    'class_id': class_id,
                                                    'confidence': confidence,
                                                    'bbox': bbox
                                                })
                                            else:
                                                # Convert to pixel coordinates
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
                    return []
                
                return detections
        except Exception as e:
            print(f"Process frame error: {e}")
            traceback.print_exc()
            return []
    
    @timing_decorator(verbose=False)
    def processing_thread(self):
        """Thread for processing frames with IMX500."""
        try:
            while not self.stop_event.is_set():
                try:
                    # Get frame from queue with timeout
                    frame = self.frame_queue.get(timeout=0.1)
                    
                    # Process frame
                    start_time = time.time()
                    detections = self.process_frame(frame)
                    
                    # Record processing time
                    if ENABLE_PROFILING:
                        processing_time = time.time() - start_time
                        performance_tracker.record('processing_time', processing_time)
                    
                    # Update latest results with lock
                    with self.lock:
                        self.latest_results = detections
                    
                    # Put in result queue (non-blocking)
                    if not self.result_queue.full():
                        self.result_queue.put((frame, detections), block=False)
                    
                except queue.Empty:
                    pass  # No frames available
                    
        except Exception as e:
            print(f"Processing thread error: {e}")
            traceback.print_exc()
            self.stop_event.set()
    
    @timing_decorator(verbose=False)
    def draw_detections(self, frame, detections):
        """
        Draw detection boxes and labels on the frame.
        
        Args:
            frame: Input frame
            detections: Detection results
            
        Returns:
            Frame with detections drawn
        """
        # Prepare boxes and labels for optimized drawing
        boxes = []
        labels = []
        colors = []
        
        for detection in detections:
            # Get detection info
            class_id = detection.get('class_id', 0)
            confidence = detection.get('confidence', 0)
            bbox = detection.get('bbox', [0, 0, 0, 0])  # [x1, y1, x2, y2]
            
            # Get label with caching
            label = get_cached_label(self.labels, class_id, "Unknown")
            label_text = f"{label} ({confidence:.2f})"
            
            # Add to lists
            boxes.append(bbox)
            labels.append(label_text)
            colors.append((0, 255, 0))  # Green
        
        # Use optimized drawing if available
        if boxes:
            try:
                # Convert boxes to numpy array for optimization
                boxes_array = np.array(boxes)
                
                # Draw boxes efficiently
                return draw_optimized_boxes(frame, boxes_array, labels, colors)
            except Exception:
                # Fall back to standard drawing
                pass
        
        # Standard drawing fallback
        result = frame.copy()
        for detection in detections:
            # Get detection info
            class_id = detection.get('class_id', 0)
            confidence = detection.get('confidence', 0)
            bbox = detection.get('bbox', [0, 0, 0, 0])  # [x1, y1, x2, y2]
            
            # Get label
            label = get_cached_label(self.labels, class_id, "Unknown")
            
            # Draw bounding box
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            cv2.rectangle(result, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label with confidence
            label_text = f"{label} ({confidence:.2f})"
            cv2.putText(result, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return result
    
    @timing_decorator(verbose=False)
    def display_thread(self):
        """Thread for displaying the processed frames with detection results."""
        last_update_time = 0
        display_interval = 1.0 / 30  # Max 30 FPS for display
        
        try:
            while not self.stop_event.is_set():
                current_time = time.time()
                
                # Limit display updates for efficiency
                if current_time - last_update_time < display_interval:
                    time.sleep(0.001)  # Short sleep
                    continue
                
                try:
                    # Try to get a processed frame from the queue
                    frame, detections = self.result_queue.get(timeout=0.1)
                    
                    # Draw detection results
                    display_frame = self.draw_detections(frame, detections)
                    
                    # Show frame
                    cv2.imshow("IMX500 Object Detection", display_frame)
                    
                    # Exit if 'q' pressed
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.stop_event.set()
                    
                    # Update timing
                    last_update_time = time.time()
                    if ENABLE_PROFILING:
                        performance_tracker.record('display_fps', 1.0 / (last_update_time - current_time))
                    
                except queue.Empty:
                    # If no new frame, use the latest frame and results
                    with self.lock:
                        if self.latest_frame is not None:
                            # Draw detection results
                            display_frame = self.draw_detections(self.latest_frame, self.latest_results)
                            
                            # Show frame
                            cv2.imshow("IMX500 Object Detection", display_frame)
                            
                            # Exit if 'q' pressed
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                self.stop_event.set()
                            
                            # Update timing
                            last_update_time = time.time()
                
        except Exception as e:
            print(f"Display thread error: {e}")
            traceback.print_exc()
            self.stop_event.set()
    
    @timing_decorator(verbose=False)
    def run(self):
        """Run the object detection application."""
        if not self.initialize():
            return
        
        # Clear stop event
        self.stop_event.clear()
        
        # Start worker pool
        self.worker_pool.start()
        
        # Create and start threads
        threads = []
        threads.append(Thread(target=self.capture_thread, daemon=True))
        threads.append(Thread(target=self.processing_thread, daemon=True))
        threads.append(Thread(target=self.display_thread, daemon=True))
        
        for thread in threads:
            thread.start()
        
        try:
            # Wait for stop event or user interruption
            while not self.stop_event.is_set():
                time.sleep(0.1)
                
                # Print performance stats if profiling is enabled
                if ENABLE_PROFILING and time.time() % 5 < 0.1:  # Every ~5 seconds
                    self.print_performance_stats()
                
        except KeyboardInterrupt:
            print("\nStopping application...")
            self.stop_event.set()
        
        # Wait for threads to finish
        for thread in threads:
            thread.join(timeout=1.0)
        
        # Stop worker pool
        self.worker_pool.stop()
        
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
        
        # Optimize memory if requested
        if self.args.optimize_memory:
            optimize_memory()
            
        print("Application stopped")
    
    def print_performance_stats(self):
        """Print performance statistics."""
        if not ENABLE_PROFILING:
            return
            
        # Get performance stats
        capture_fps_stats = performance_tracker.get_stats('capture_fps')
        processing_time_stats = performance_tracker.get_stats('processing_time')
        display_fps_stats = performance_tracker.get_stats('display_fps')
        
        # Print stats
        print("\n--- Performance Statistics ---")
        if capture_fps_stats['count'] > 0:
            print(f"Capture FPS: {capture_fps_stats['mean']:.2f} (min: {capture_fps_stats['min']:.2f}, max: {capture_fps_stats['max']:.2f})")
        if processing_time_stats['count'] > 0:
            print(f"Processing Time: {processing_time_stats['mean']*1000:.2f} ms (min: {processing_time_stats['min']*1000:.2f} ms, max: {processing_time_stats['max']*1000:.2f} ms)")
        if display_fps_stats['count'] > 0:
            print(f"Display FPS: {display_fps_stats['mean']:.2f} (min: {display_fps_stats['min']:.2f}, max: {display_fps_stats['max']:.2f})")
        print("-----------------------------\n")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Optimized IMX500 Object Detection Demo")
    parser.add_argument("--model", required=True, help="Path to the model file (.rpk)")
    parser.add_argument("--labels", required=True, help="Path to the labels file")
    parser.add_argument("--fps", type=int, default=25, help="Frames per second (default: 25)")
    parser.add_argument("--display-width", type=int, default=640, help="Display width (default: 640)")
    parser.add_argument("--display-height", type=int, default=480, help="Display height (default: 480)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Detection threshold (default: 0.5)")
    parser.add_argument("--bbox-normalization", action="store_true", help="Use normalized bounding box coordinates")
    parser.add_argument("--ignore-dash-labels", action="store_true", help="Ignore labels starting with '-'")
    parser.add_argument("--workers", type=int, help="Number of worker threads (default: auto)")
    parser.add_argument("--profile", action="store_true", help="Enable performance profiling")
    parser.add_argument("--optimize-memory", action="store_true", help="Enable memory optimizations")
    
    return parser.parse_args()

def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Create and run the application
    app = OptimizedDetectionApp(args)
    
    # Measure total runtime
    with Timer("Total runtime", verbose=args.profile):
        app.run()

if __name__ == "__main__":
    main()
