"""Utility to detect and test available cameras."""

import cv2
import sys
import time


def detect_cameras(max_index: int = 10) -> list[dict]:
    """Detect available cameras and their properties.

    Args:
        max_index: Maximum camera index to check.

    Returns:
        List of dictionaries with camera info.
    """
    cameras = []

    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            backend = cap.get(cv2.CAP_PROP_BACKEND)

            cameras.append({
                "index": i,
                "width": width,
                "height": height,
                "fps": fps,
                "backend": backend,
            })
            cap.release()

    return cameras


def test_camera(device_id: int, duration: int = 3) -> bool:
    """Test a camera by capturing frames.

    Args:
        device_id: Camera device index.
        duration: Duration to test in seconds.

    Returns:
        True if camera works, False otherwise.
    """
    cap = cv2.VideoCapture(device_id)

    if not cap.isOpened():
        print(f"✗ Camera {device_id}: Failed to open")
        return False

    print(f"✓ Camera {device_id}: Opened successfully")

    # Try to capture some frames
    success_count = 0
    start_time = time.time()

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if ret:
            success_count += 1
        else:
            print(f"  Warning: Frame read failed")

        # Small display for visual feedback
        if success_count % 15 == 0:
            print(f"  ✓ Captured {success_count} frames...")

    cap.release()

    if success_count > 0:
        print(f"✓ Camera {device_id}: Successfully captured {success_count} frames")
        return True
    else:
        print(f"✗ Camera {device_id}: No frames captured")
        return False


def main() -> int:
    """Main entry point."""
    print("=" * 60)
    print("Camera Detector & Tester")
    print("=" * 60)
    print()

    # Detect cameras
    print("Scanning for available cameras...")
    cameras = detect_cameras()

    if not cameras:
        print("✗ No cameras detected!")
        return 1

    print(f"\n✓ Found {len(cameras)} camera(s):\n")

    # Display camera info
    for cam in cameras:
        print(f"Camera {cam['index']}:")
        print(f"  Resolution: {cam['width']}x{cam['height']}")
        print(f"  FPS: {cam['fps']:.1f}")
        print(f"  Backend: {int(cam['backend'])}")

    # Test each camera
    print("\n" + "=" * 60)
    print("Testing cameras (3 seconds each)...")
    print("=" * 60)

    working_cameras = []
    for cam in cameras:
        idx = cam['index']
        print(f"\nTesting camera {idx}...")
        if test_camera(idx):
            working_cameras.append(idx)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total detected: {len(cameras)}")
    print(f"Working cameras: {working_cameras}")

    if working_cameras:
        print("\nUsage:")
        for idx in working_cameras:
            print(f"  python main.py --camera {idx}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
