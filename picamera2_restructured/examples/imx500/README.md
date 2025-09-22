# IMX500 Object Detection with PiCamera2 Restructured

This directory contains examples for using the Sony IMX500 intelligent vision sensor with the restructured PiCamera2 library.

## Object Detection Demo

The `object_detection_demo.py` script provides a complete example of object detection using the IMX500's AI capabilities.

### Prerequisites

1. Sony IMX500 camera module connected to your Raspberry Pi
2. A compatible model file (.rpk format)
3. A labels file with class names

### Usage

```bash
python object_detection_demo.py --model /path/to/model.rpk --labels /path/to/labels.txt [options]
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--model` | Path to the model file (.rpk) | Required |
| `--labels` | Path to the labels file | Required |
| `--fps` | Frames per second | 25 |
| `--display-width` | Display width | 640 |
| `--display-height` | Display height | 480 |
| `--threshold` | Detection threshold | 0.5 |
| `--bbox-normalization` | Use normalized bounding box coordinates | False |
| `--ignore-dash-labels` | Ignore labels starting with '-' | False |

### Example Command

The following command runs object detection with a 25 FPS display rate, using normalized bounding box coordinates and ignoring labels that start with a dash:

```bash
python object_detection_demo.py --model /home/admin/AI/network.rpk --labels /home/admin/AI/labels.txt --fps 25 --bbox-normalization --ignore-dash-labels
```

### How It Works

The script uses multi-threading to optimize performance:

1. **Capture Thread**: Continuously captures frames from the camera
2. **Processing Thread**: Processes frames using the IMX500 AI capabilities
3. **Display Thread**: Shows the results with bounding boxes and labels

This approach ensures smooth performance by separating capture, processing, and display operations.

### Controls

- Press 'q' to quit the application

### Customizing the Script

You can modify the script to:

- Save detected objects to files
- Process video files instead of camera input
- Implement custom post-processing of detected objects
- Stream the results over a network

## Troubleshooting

### Model Loading Issues

If the model fails to load, check:
- The model file path is correct
- The model is compatible with IMX500
- You have sufficient permissions to access the file

### Detection Issues

If detections are not showing up:
- Try lowering the detection threshold (e.g., `--threshold 0.3`)
- Ensure the labels file matches the model's classes
- Check if the IMX500 device is properly recognized
