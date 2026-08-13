# Enhanced Gesture Control UI Guide

## Overview

The enhanced interface provides real-time camera switching, gesture information display, and detailed statistics about hand detection and recognized gestures.

## Starting the Application

### With Enhanced UI (Recommended)
```bash
python main_enhanced.py
```

### Original Version
```bash
python main.py
```

## Features

### 1. **Camera Switching**
- **Press C** to cycle through available cameras
- Automatically detects:
  - Built-in laptop camera (Camera 0)
  - USB/External cameras (Camera 1, 2, etc.)
  - Phone camera via USB connection

**Note:** To use your phone camera:
1. Connect your phone via USB
2. Enable USB debugging/camera sharing on your phone
3. Use an app like **DroidCam**, **IP Webcam**, or similar to stream the camera

### 2. **Information Panel**
Located on the right side of the screen, displays:

#### Camera Information
- Currently active camera name
- Available cameras count

#### Hand Detection
- Number of hands detected (0-2)
- Gesture name for each hand
- Which fingers are extended (T=Thumb, I=Index, M=Middle, R=Ring, P=Pinky)
  - ✓ = Extended
  - ✗ = Folded

#### Gesture Details
For each detected hand, shows:
- **Gesture name** (e.g., "Mano Abierta", "Señalar")
- **Hand side** (R for Right, L for Left)
- **Finger states** (visual indicator of which fingers are up)
- **Mapped action** (if configured)

#### Statistics
- Current FPS (frames per second)
- Last recognized gesture

### 3. **Status Bar**
Bottom of screen shows available keyboard shortcuts:
```
Q: salir  |  R: resetear  |  C: cambiar cámara  |  I: info
```

### 4. **Action Toast**
When a gesture triggers an action, a notification appears in the center:
```
Mano Abierta  →  SPACE
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Q** | Quit application |
| **R** | Reset gesture dispatcher state |
| **C** | Change to next available camera |
| **I** | Toggle information panel (future) |

## Advanced Options

### Use Specific Camera
```bash
python main_enhanced.py --camera 1
```

### Detection Only (No Actions)
```bash
python main_enhanced.py --no-actions
```

### Debug Mode
Shows wrist coordinates:
```bash
python main_enhanced.py --debug
```

### Combine Options
```bash
python main_enhanced.py --camera 1 --debug --no-actions
```

## Finger State Legend

In the information panel, fingers are shown as:
- **T** - Thumb
- **I** - Index (pointer finger)
- **M** - Middle finger
- **R** - Ring finger
- **P** - Pinky finger

Example: `Fingers: ✓ ✗ ✗ ✗ ✗` means only the thumb is extended.

## Gesture Reference

| Gesture | Fingers | Icon |
|---------|---------|------|
| Fist (Puño) | All closed | ✗ ✗ ✗ ✗ ✗ |
| Open Hand (Mano Abierta) | All open | ✓ ✓ ✓ ✓ ✓ |
| Point (Señalar) | Index only | ✗ ✓ ✗ ✗ ✗ |
| Victory | Index + Middle | ✗ ✓ ✓ ✗ ✗ |
| Rock | Index + Pinky | ✗ ✓ ✗ ✗ ✓ |
| Thumbs Up | Thumb up | ✓ ✗ ✗ ✗ ✗ |
| Thumbs Down | Thumb down | ✓ ✗ ✗ ✗ ✗ |
| OK | Thumb+Index close, other open | ✓ ✓ ✓ ✓ ✓ |

## Troubleshooting

### Camera Not Detected
1. Check if camera is connected
2. Try different device indices:
   ```bash
   python main_enhanced.py --camera 1
   python main_enhanced.py --camera 2
   ```
3. Check system camera permissions
4. Restart the application

### Phone Camera Setup

**DroidCam (Recommended)**
1. Download DroidCam on your Android phone
2. Connect phone to same WiFi as laptop
3. Note the IP address shown in DroidCam
4. Your phone camera will appear as a standard USB device

**IP Webcam**
1. Download IP Webcam on your phone
2. Start the app and note the IP:PORT
3. OpenCV can access it via `http://IP:PORT/video`

### Performance Issues
- Lower resolution in `config/settings.yaml`:
  ```yaml
  camera:
    width: 640
    height: 480
  ```
- Reduce `max_num_hands` if tracking one hand is enough
- Close other applications using your camera

## Configuration

Edit `config/settings.yaml` to customize:

```yaml
camera:
  device_id: 0              # Default camera
  width: 1280               # Resolution
  height: 720
  backend: dshow            # Windows DirectShow

renderer:
  show_landmarks: true      # Draw hand skeleton
  show_fps: true           # Show FPS counter
  show_gesture_label: true # Show gesture name
  show_info_panel: true    # Show right-side info panel
  font_scale: 0.9
  overlay_alpha: 0.55      # Transparency (0-1)

mediapipe:
  max_num_hands: 2         # Detect 1 or 2 hands
  min_detection_confidence: 0.75
  min_tracking_confidence: 0.65
```

## Performance Tips

1. **Close Unnecessary Applications** - Reduces CPU load
2. **Lower Resolution** - Use 640x480 instead of 1280x720
3. **Single Hand Tracking** - Set `max_num_hands: 1` if not needed
4. **Disable Panel** - Set `show_info_panel: false` for minimal overhead

## Tips for Best Detection

1. **Lighting** - Good natural or artificial lighting
2. **Hand Position** - Keep hands in frame and at comfortable distance
3. **Background** - Contrast between hands and background helps
4. **Steady Hands** - Avoid rapid movements for stable detection
5. **Distance** - Optimal distance: 30cm - 1 meter from camera

## Next Steps

- Customize gesture mappings in `config/mappings.yaml`
- Train custom gestures using `python tools/collect_data.py`
- Create actions for detected gestures
- Experiment with different hand distances and angles
