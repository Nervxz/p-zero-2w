#!/usr/bin/env python3

"""
Fixed IMX500 Object Detection Demo using the PiCamera2 Restructured API

This script demonstrates object detection using the Sony IMX500 intelligent
vision sensor with embedded AI processing. It's designed to work reliably
with the IMX500 camera by closely following the original implementation.

Usage:
    python fixed_detection_demo.py --model /path/to/model.rpk --labels /path/to/labels.txt [options]

Options:
    --model MODEL       Path to the model file (.rpk)
    --labels LABELS     Path to the labels file
    --fps FPS           Frames per second (default: 25)
    --threshold T       Detection threshold (default: 0.55)
    --iou IOU           IOU threshold (default: 0.65)
    --max-detections N  Maximum number of detections (default: 10)
    --bbox-normalization Use normalized bounding box coordinates
    --ignore-dash-labels Ignore labels starting with '-'
"""

import argparse
import cv2
import numpy as np
import time
import os
import sys
import threading
import queue
from functools import lru_cache

# Add both the restructured library and original picamera2 to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import original picamera2 for IMX500 support
original_picamera2_dir = os.path.abspath(os.path.join(root_dir, 'picamera2'))
if original_picamera2_dir not in sys.path:
    sys.path.append(original_picamera2_dir)

# Import from picamera2 - this is the ONLY version that works reliably with IMX500
from picamera2 import MappedArray, Picamera2
from picamera2.devices import IMX500
try:
    from picamera2.devices.imx500 import NetworkIntrinsics, postprocess_nanodet_detection
except ImportError:
    print("Warning: Could not import some IMX500 modules")

# Detection class matching the original implementation
class Detection:
    def __init__(self, coords, category, conf, metadata, imx500_device, camera):
        """Create a Detection object, recording the bounding box, category and confidence."""
        self.category = category
        self.conf = conf
        self.box = imx500_device.convert_inference_coords(coords, metadata, camera)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fixed IMX500 Object Detection Demo")
    parser.add_argument("--model", required=True, help="Path to the model file (.rpk)")
    parser.add_argument("--labels", required=True, help="Path to the labels file")
    parser.add_argument("--fps", type=int, default=25, help="Frames per second (default: 25)")
    parser.add_argument("--threshold", type=float, default=0.55, help="Detection threshold (default: 0.55)")
    parser.add_argument("--iou", type=float, default=0.65, help="IOU threshold (default: 0.65)")
    parser.add_argument("--max-detections", type=int, default=10, help="Maximum number of detections (default: 10)")
    parser.add_argument("--bbox-normalization", action="store_true", help="Use normalized bounding box coordinates")
    parser.add_argument("--ignore-dash-labels", action="store_true", help="Ignore labels starting with '-'")
    parser.add_argument("--postprocess", choices=["", "nanodet"], default=None, help="Run post process of type")
    parser.add_argument("-r", "--preserve-aspect-ratio", action="store_true", help="Preserve aspect ratio of input tensor")
    
    return parser.parse_args()

def parse_detections(metadata, imx500_device, camera, args, intrinsics):
    """Parse the output tensor into a number of detected objects, scaled to the ISP output."""
    bbox_normalization = intrinsics.bbox_normalization if hasattr(intrinsics, 'bbox_normalization') else args.bbox_normalization
    threshold = args.threshold
    iou = args.iou
    max_detections = args.max_detections

    np_outputs = imx500_device.get_outputs(metadata, add_batch=True)
    input_w, input_h = imx500_device.get_input_size()
    
    if np_outputs is None:
        return None
        
    # Handle different postprocessing methods
    postprocess_type = args.postprocess
    if hasattr(intrinsics, 'postprocess') and intrinsics.postprocess:
        postprocess_type = intrinsics.postprocess
        
    if postprocess_type == "nanodet":
        try:
            boxes, scores, classes = postprocess_nanodet_detection(
                outputs=np_outputs[0], 
                conf=threshold, 
                iou_thres=iou,
                max_out_dets=max_detections
            )[0]
            
            from picamera2.devices.imx500.postprocess import scale_boxes
            boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
        except Exception as e:
            print(f"Error in nanodet processing: {e}")
            import traceback
            traceback.print_exc()
            return None
    else:
        # Standard processing
        boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
        if bbox_normalization:
            boxes = boxes / input_h

        boxes = np.array_split(boxes, 4, axis=1)
        boxes = list(zip(*boxes))

    # Create detection objects exactly like the original implementation
    detections = [
        Detection(box, category, score, metadata, imx500_device, camera)
        for box, score, category in zip(boxes, scores, classes)
        if score > threshold
    ]
    
    return detections

@lru_cache(maxsize=32)
def get_labels(labels_tuple, ignore_dash_labels=False):
    """Get cached labels."""
    if ignore_dash_labels:
        return [label for label in labels_tuple if label and label != "-"]
    return list(labels_tuple)

def draw_detections(frame, detections, labels):
    """Draw detections on a regular frame (not a request)."""
    if not detections:
        return frame
        
    # Make a copy of the frame
    result = frame.copy()
    
    for detection in detections:
        x, y, w, h = detection.box
        label = f"{labels[int(detection.category)]} ({detection.conf:.2f})"

        # Calculate text size and position
        (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        text_x = x + 5
        text_y = y + 15

        # Draw background rectangle for text
        cv2.rectangle(result,
                      (text_x, text_y - text_height),
                      (text_x + text_width, text_y + baseline),
                      (0, 0, 0), -1)  # Black background

        # Draw text
        cv2.putText(result, label, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)  # Yellow text

        # Draw detection box
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), thickness=2)

    return result

def draw_detections_on_request(request, detections, labels, preserve_aspect_ratio=False, imx500_device=None):
    """Draw the detections for this request onto the ISP output."""
    if not detections:
        return
        
    with MappedArray(request, 'main') as m:
        for detection in detections:
            x, y, w, h = detection.box
            label = f"{labels[int(detection.category)]} ({detection.conf:.2f})"

            # Calculate text size and position
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            text_x = x + 5
            text_y = y + 15

            # Create a copy of the array to draw the background with opacity
            overlay = m.array.copy()

            # Draw the background rectangle on the overlay
            cv2.rectangle(overlay,
                          (text_x, text_y - text_height),
                          (text_x + text_width, text_y + baseline),
                          (255, 255, 255),  # Background color (white)
                          cv2.FILLED)

            alpha = 0.3
            cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)

            # Draw text on top of the background
            cv2.putText(m.array, label, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # Draw detection box
            cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0), thickness=2)

        # Draw ROI if preserve_aspect_ratio is enabled
        if preserve_aspect_ratio and imx500_device:
            try:
                b_x, b_y, b_w, b_h = imx500_device.get_roi_scaled(request)
                color = (255, 0, 0)  # red
                cv2.putText(m.array, "ROI", (b_x + 5, b_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                cv2.rectangle(m.array, (b_x, b_y), (b_x + b_w, b_y + b_h), (255, 0, 0, 0))
            except Exception as e:
                print(f"Error drawing ROI: {e}")

def detection_worker(jobs_queue, results_queue, imx500_device, camera, args, intrinsics, stop_event):
    """Worker thread for handling detections."""
    while not stop_event.is_set():
        try:
            # Get the next request to process
            try:
                request = jobs_queue.get(timeout=0.5)
            except queue.Empty:
                continue
                
            if request is None:
                break  # Exit signal
                
            # Get metadata from the request
            metadata = request.get_metadata()
            if metadata:
                # Process detections
                detections = parse_detections(metadata, imx500_device, camera, args, intrinsics)
                
                # Put results in the queue
                results_queue.put((request, detections))
            else:
                # No metadata, release the request
                request.release()
                
        except Exception as e:
            print(f"Error in detection worker: {e}")
            import traceback
            traceback.print_exc()

def display_worker(results_queue, stop_event, imx500_device, args, labels):
    """Worker thread for displaying results."""
    last_detections = []
    
    while not stop_event.is_set():
        try:
            # Get the next result to display
            try:
                request, detections = results_queue.get(timeout=0.5)
            except queue.Empty:
                continue
                
            # Use last detections if current ones are None
            if detections is None:
                detections = last_detections
            else:
                last_detections = detections
                
            # Draw detections directly on the request
            draw_detections_on_request(
                request, 
                detections, 
                labels, 
                preserve_aspect_ratio=args.preserve_aspect_ratio,
                imx500_device=imx500_device
            )
            
            # Display the image
            with MappedArray(request, 'main') as m:
                cv2.imshow('IMX500 Object Detection', m.array)
                cv2.waitKey(1)
            
            # Release the request
            request.release()
            
        except Exception as e:
            print(f"Error in display worker: {e}")
            import traceback
            traceback.print_exc()

def main():
    # Parse arguments
    args = parse_args()
    
    print(f"Loading model: {args.model}")
    
    # This must be called before instantiation of Picamera2
    imx500 = IMX500(args.model)
    
    # Get network intrinsics
    intrinsics = None
    if hasattr(imx500, 'network_intrinsics'):
        intrinsics = imx500.network_intrinsics
        if not intrinsics:
            intrinsics = NetworkIntrinsics()
            intrinsics.task = "object detection"
        elif intrinsics.task != "object detection":
            print("Network is not an object detection task", file=sys.stderr)
            exit()
            
        # Override intrinsics from args
        for key, value in vars(args).items():
            if key == 'labels' and value is not None:
                with open(value, 'r') as f:
                    intrinsics.labels = f.read().splitlines()
            elif hasattr(intrinsics, key) and value is not None:
                setattr(intrinsics, key, value)
                
        # Set defaults
        if intrinsics.labels is None:
            try:
                with open("assets/coco_labels.txt", "r") as f:
                    intrinsics.labels = f.read().splitlines()
            except FileNotFoundError:
                print("Warning: Could not find default labels file")
                intrinsics.labels = []
                
        if hasattr(intrinsics, 'update_with_defaults'):
            intrinsics.update_with_defaults()
    
    # Load labels from file if provided
    labels = []
    if args.labels:
        try:
            with open(args.labels, 'r') as f:
                labels = f.read().splitlines()
        except Exception as e:
            print(f"Error loading labels: {e}")
            exit(1)
    elif intrinsics and hasattr(intrinsics, 'labels'):
        labels = intrinsics.labels
        
    # Process labels
    if args.ignore_dash_labels:
        labels = [label for label in labels if label and label != "-"]
    
    print(f"Loaded {len(labels)} labels")
    
    # Show firmware upload progress
    if hasattr(imx500, 'show_network_fw_progress_bar'):
        print("Showing network firmware upload progress...")
        imx500.show_network_fw_progress_bar()
    
    # Initialize camera
    picam2 = Picamera2(imx500.camera_num)
    main = {'format': 'RGB888'}
    fps = args.fps
    config = picam2.create_preview_configuration(
        main, 
        controls={"FrameRate": fps},
        buffer_count=12
    )
    
    # Start camera
    picam2.start(config, show_preview=False)
    
    # Set aspect ratio if needed
    if args.preserve_aspect_ratio and hasattr(imx500, 'set_auto_aspect_ratio'):
        imx500.set_auto_aspect_ratio()
    
    # Create queues for communication
    jobs_queue = queue.Queue()
    results_queue = queue.Queue()
    stop_event = threading.Event()
    
    # Create and start workers
    detection_thread = threading.Thread(
        target=detection_worker,
        args=(jobs_queue, results_queue, imx500, picam2, args, intrinsics, stop_event),
        daemon=True
    )
    detection_thread.start()
    
    display_thread = threading.Thread(
        target=display_worker,
        args=(results_queue, stop_event, imx500, args, labels),
        daemon=True
    )
    display_thread.start()
    
    # Create a window immediately to show we're working
    cv2.namedWindow('IMX500 Object Detection', cv2.WINDOW_NORMAL)
    
    try:
        print("Detection running. Press Ctrl+C to stop.")
        last_detections = []
        
        while True:
            # Capture a request
            request = picam2.capture_request()
            
            # Put the request in the jobs queue for detection
            jobs_queue.put(request)
            
            # Also display the raw frame immediately for responsiveness
            # This ensures we always see video even if detection is slow
            with MappedArray(request, 'main') as m:
                # Make a copy for display
                frame = m.array.copy()
            
            # Draw any previous detections we have
            if last_detections:
                frame = draw_detections(frame, last_detections, labels)
            
            # Show the frame immediately
            cv2.imshow('IMX500 Object Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # Update last detections if we have new ones
            try:
                _, detections = results_queue.get_nowait()
                if detections:
                    last_detections = detections
            except queue.Empty:
                pass
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Stop workers
        stop_event.set()
        jobs_queue.put(None)  # Signal to stop
        
        # Wait for workers to finish
        detection_thread.join(timeout=1.0)
        display_thread.join(timeout=1.0)
        
        # Clean up
        cv2.destroyAllWindows()
        picam2.stop()
        picam2.close()
        
        print("Detection stopped")

if __name__ == "__main__":
    main()