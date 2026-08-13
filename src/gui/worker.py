"""Background capture + detection + gesture-recognition worker thread.

Owns CameraCapture and HandDetector — the only thread that ever touches
them. Frames and gesture results cross to the GUI thread via a bounded,
drop-oldest queue; commands cross the other way via a plain FIFO queue. No
Tk/PIL/matplotlib object is ever created or touched here.

Action dispatch (keyboard/mouse) deliberately does NOT happen on this
thread: macOS's Text Input Source Manager (used internally by pynput's
keyboard backend) asserts it is only ever called from the main thread and
raises SIGTRAP otherwise. ActionDispatcher is owned and called by
GestureControlApp on the Tk main thread instead — see src/gui/app.py.
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

from src.capture import CameraCapture
from src.detector import HandDetector
from src.gestures import GestureResult, recognize

logger = logging.getLogger(__name__)

_MP_DRAWING = mp.solutions.drawing_utils
_MP_HANDS = mp.solutions.hands


@dataclass
class FrameUpdate:
    """One frame's worth of results, handed off to the GUI thread.

    Attributes:
        frame: RGB numpy array (H x W x 3), ready for PIL/Tk display.
        gestures: Recognized gestures for this frame, one per detected hand.
        fps: Instantaneous FPS reported by CameraCapture.
        hands_count: Number of hands detected this frame.
        ts: time.monotonic() timestamp of this update.
        camera_error: Error message if the camera failed to open, else None.
    """

    frame: np.ndarray
    gestures: list[GestureResult]
    fps: float
    hands_count: int
    ts: float
    camera_error: Optional[str] = None


class CaptureWorker(threading.Thread):
    """Runs the camera-capture/detect/recognize loop on a background thread.

    Args:
        device_id: Initial camera device index.
        cam_cfg: dict with 'width', 'height', and optionally 'backend'.
        mp_cfg: dict with 'max_num_hands', 'min_detection_confidence', 'min_tracking_confidence'.
        out_queue: Queue the worker pushes FrameUpdate objects onto (drop-oldest when full).
        cmd_queue: Queue the GUI thread pushes command tuples onto.
        debug: If True, logs wrist landmark coordinates for the first detected hand each frame.
    """

    def __init__(
        self,
        device_id: int,
        cam_cfg: dict,
        mp_cfg: dict,
        out_queue: "queue.Queue[FrameUpdate]",
        cmd_queue: "queue.Queue[tuple]",
        debug: bool = False,
    ) -> None:
        super().__init__(daemon=True, name="CaptureWorker")
        self._device_id = device_id
        self._cam_cfg = cam_cfg
        self._mp_cfg = mp_cfg
        self._out_queue = out_queue
        self._cmd_queue = cmd_queue
        self._debug = debug
        self._stop_event = threading.Event()

        self._cap: Optional[CameraCapture] = None
        self._detector: Optional[HandDetector] = None

    def stop(self) -> None:
        """Signal the worker loop to exit on its next iteration."""
        self._stop_event.set()

    def run(self) -> None:
        self._detector = HandDetector(
            max_hands=self._mp_cfg["max_num_hands"],
            min_detection_conf=self._mp_cfg["min_detection_confidence"],
            min_tracking_conf=self._mp_cfg["min_tracking_confidence"],
        )
        self._open_camera(self._device_id)

        try:
            while not self._stop_event.is_set():
                self._drain_commands()
                self._tick()
        finally:
            if self._cap:
                self._cap.release()
            if self._detector:
                self._detector.close()
            logger.info("CaptureWorker stopped")

    def _open_camera(self, device_id: int) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None
        try:
            self._cap = CameraCapture(
                device_id=device_id,
                width=self._cam_cfg["width"],
                height=self._cam_cfg["height"],
                backend=self._cam_cfg.get("backend", ""),
            )
            self._device_id = device_id
            logger.info("Camera %d opened", device_id)
        except RuntimeError as exc:
            logger.error("Failed to open camera %d: %s", device_id, exc)
            self._push_error(str(exc))

    def _drain_commands(self) -> None:
        while True:
            try:
                cmd = self._cmd_queue.get_nowait()
            except queue.Empty:
                return
            self._handle_command(cmd)

    def _handle_command(self, cmd: tuple) -> None:
        name = cmd[0]
        if name == "switch_camera":
            self._open_camera(cmd[1])
        elif name == "stop":
            self._stop_event.set()
        else:
            logger.warning("Unknown worker command: %s", cmd)

    def _tick(self) -> None:
        if self._cap is None:
            time.sleep(0.2)
            return

        ret, frame_bgr = self._cap.read()
        if not ret:
            time.sleep(0.05)
            return

        rgb_for_detection = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        detection = self._detector.detect(rgb_for_detection)
        gestures = [recognize(hand) for hand in detection.hands]

        if self._debug and detection.hands:
            wrist = detection.hands[0].landmarks[0]
            logger.info("Wrist: (%.3f, %.3f, %.3f)", wrist.x, wrist.y, wrist.z)

        display_bgr = frame_bgr
        if detection.raw_result.multi_hand_landmarks:
            display_bgr = frame_bgr.copy()
            for hand_lm in detection.raw_result.multi_hand_landmarks:
                _MP_DRAWING.draw_landmarks(
                    display_bgr,
                    hand_lm,
                    _MP_HANDS.HAND_CONNECTIONS,
                    _MP_DRAWING.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                    _MP_DRAWING.DrawingSpec(color=(250, 44, 250), thickness=2),
                )

        update = FrameUpdate(
            frame=cv2.cvtColor(display_bgr, cv2.COLOR_BGR2RGB),
            gestures=gestures,
            fps=self._cap.get_fps(),
            hands_count=len(detection.hands),
            ts=time.monotonic(),
        )
        self._push_update(update)

    def _push_update(self, update: FrameUpdate) -> None:
        try:
            self._out_queue.put_nowait(update)
        except queue.Full:
            try:
                self._out_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._out_queue.put_nowait(update)
            except queue.Full:
                pass

    def _push_error(self, message: str) -> None:
        update = FrameUpdate(
            frame=np.zeros((480, 640, 3), dtype=np.uint8),
            gestures=[],
            fps=0.0,
            hands_count=0,
            ts=time.monotonic(),
            camera_error=message,
        )
        self._push_update(update)
