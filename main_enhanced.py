"""
Gesture Control — Enhanced entry point with camera selection UI.

Usage:
    python main_enhanced.py                  # default camera
    python main_enhanced.py --camera 1       # specific camera index
    python main_enhanced.py --no-actions     # detection only, no keyboard/mouse control
    python main_enhanced.py --debug          # show landmark coordinates overlay
"""

import argparse
import logging
import sys
import threading
import queue

import cv2
import yaml


def _setup_logging(level_str: str = "INFO") -> None:
    level = getattr(logging, level_str.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _load_settings(path: str = "config/settings.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-time hand gesture control")
    parser.add_argument("--camera", type=int, default=None, help="Camera device index")
    parser.add_argument("--no-actions", action="store_true", help="Disable keyboard/mouse actions")
    parser.add_argument("--debug", action="store_true", help="Show landmark coordinates")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    try:
        settings = _load_settings()
    except FileNotFoundError:
        print("ERROR: config/settings.yaml not found. Run from the project root.", file=sys.stderr)
        return 1
    except yaml.YAMLError as exc:
        print(f"ERROR: Invalid settings.yaml — {exc}", file=sys.stderr)
        return 1

    log_level = settings.get("logging", {}).get("level", "INFO")
    _setup_logging(log_level)
    logger = logging.getLogger(__name__)

    cam_cfg = settings["camera"]
    mp_cfg = settings["mediapipe"]
    renderer_cfg = settings["renderer"]

    device_id = args.camera if args.camera is not None else cam_cfg["device_id"]

    # Lazy imports after logging is configured
    from src.capture import CameraCapture
    from src.detector import HandDetector
    from src.gestures import recognize
    from src.renderer import Renderer
    from src.ui.camera_control import CameraSelector

    # Camera selector
    camera_selector = CameraSelector(device_id)
    available_cameras = camera_selector.available_cameras

    if not available_cameras:
        logger.error("No cameras detected")
        return 1

    logger.info(f"Available cameras: {available_cameras}")

    dispatcher = None
    if not args.no_actions:
        try:
            from src.actions import ActionDispatcher
            dispatcher = ActionDispatcher("config/mappings.yaml")
        except FileNotFoundError:
            logger.warning("mappings.yaml not found — actions disabled")
        except Exception as exc:
            logger.warning("ActionDispatcher init failed: %s — actions disabled", exc)

    # Initialize camera capture
    cap = None
    try:
        cap = CameraCapture(
            device_id=camera_selector.current_device_id,
            width=cam_cfg["width"],
            height=cam_cfg["height"],
            backend=cam_cfg.get("backend", "dshow"),
        )
    except RuntimeError as exc:
        logger.error("%s", exc)
        return 1

    detector = HandDetector(
        max_hands=mp_cfg["max_num_hands"],
        min_detection_conf=mp_cfg["min_detection_confidence"],
        min_tracking_conf=mp_cfg["min_tracking_confidence"],
    )
    renderer = Renderer(renderer_cfg)
    renderer.set_camera_name(camera_selector.get_camera_name(camera_selector.current_device_id))

    logger.info("Starting gesture control loop. Press Q to quit, C to change camera.")

    camera_change_queue = queue.Queue()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Camera read failed — exiting")
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            detection = detector.detect(rgb)

            gesture_results = [recognize(hand) for hand in detection.hands]

            if dispatcher:
                for gesture in gesture_results:
                    result = dispatcher.dispatch(gesture)
                    if result:
                        renderer.notify_action(*result)

            fps = cap.get_fps()
            output = renderer.draw(frame, detection, gesture_results, fps)

            if args.debug and detection.hands:
                for hand in detection.hands:
                    lm = hand.landmarks[0]
                    debug_txt = f"Wrist: ({lm.x:.3f}, {lm.y:.3f}, {lm.z:.3f})"
                    cv2.putText(output, debug_txt, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            cv2.imshow("Gesture Control — Enhanced", output)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                logger.info("Quit requested")
                break
            elif key == ord("r"):
                logger.info("Reset requested")
                if dispatcher:
                    dispatcher._last_dispatch.clear()
            elif key == ord("c"):
                logger.info("Camera change requested")
                # Cycle through available cameras
                current_idx = available_cameras.index(camera_selector.current_device_id)
                next_idx = (current_idx + 1) % len(available_cameras)
                next_camera = available_cameras[next_idx]

                # Close current camera and open new one
                cap.release()
                logger.info(f"Switching to camera {next_camera}")

                try:
                    cap = CameraCapture(
                        device_id=next_camera,
                        width=cam_cfg["width"],
                        height=cam_cfg["height"],
                        backend=cam_cfg.get("backend", "dshow"),
                    )
                    camera_selector.switch_camera(next_camera)
                    renderer.set_camera_name(camera_selector.get_camera_name(next_camera))
                    logger.info(f"Switched to {camera_selector.get_camera_name(next_camera)}")
                except RuntimeError as exc:
                    logger.error(f"Failed to switch camera: {exc}")
                    # Try to reopen previous camera
                    try:
                        cap = CameraCapture(
                            device_id=camera_selector.current_device_id,
                            width=cam_cfg["width"],
                            height=cam_cfg["height"],
                            backend=cam_cfg.get("backend", "dshow"),
                        )
                    except RuntimeError:
                        logger.error("Failed to restore previous camera")
                        break

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        if cap:
            cap.release()
        detector.close()
        cv2.destroyAllWindows()
        logger.info("Shutdown complete")

    return 0


if __name__ == "__main__":
    sys.exit(main())
