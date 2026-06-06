"""Webcam capture module with horizontal flip and FPS tracking."""

import logging
import time
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


_BACKENDS: dict[str, int] = {
    "dshow": cv2.CAP_DSHOW,   # DirectShow — recommended for Windows
    "msmf": cv2.CAP_MSMF,     # Media Foundation — alternative Windows backend
    "v4l2": cv2.CAP_V4L2,     # Linux
    "": cv2.CAP_ANY,           # auto-detect
}


class CameraCapture:
    """Manages webcam capture with mirroring and real-time FPS calculation.

    Args:
        device_id: Camera device index (default 0).
        width: Desired frame width in pixels.
        height: Desired frame height in pixels.
        backend: Camera backend name — 'dshow' (Windows), 'msmf', 'v4l2', or '' (auto).
    """

    def __init__(
        self,
        device_id: int = 0,
        width: int = 1280,
        height: int = 720,
        backend: str = "dshow",
    ) -> None:
        self._device_id = device_id
        self._width = width
        self._height = height
        self._backend = _BACKENDS.get(backend.lower(), cv2.CAP_DSHOW)
        self._cap: Optional[cv2.VideoCapture] = None
        self._last_frame_time: float = 0.0
        self._fps: float = 0.0
        self._open()

    def _open(self) -> None:
        """Open the camera device with the configured backend and resolution."""
        self._cap = cv2.VideoCapture(self._device_id, self._backend)
        if not self._cap.isOpened():
            # Fallback: try without explicit backend
            logger.warning(
                "Camera %d failed with backend %d — retrying with auto-detect",
                self._device_id,
                self._backend,
            )
            self._cap = cv2.VideoCapture(self._device_id)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera device {self._device_id}. "
                "Check that a webcam is connected and not used by another app "
                "(Teams, Zoom, OBS, etc.)."
            )
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        logger.info("Camera %d opened (%dx%d)", self._device_id, self._width, self._height)

    def read(self) -> tuple[bool, np.ndarray]:
        """Read a single frame, already horizontally flipped (mirror mode).

        Returns:
            Tuple of (success, frame). Frame is BGR numpy array.
        """
        if self._cap is None or not self._cap.isOpened():
            return False, np.zeros((self._height, self._width, 3), dtype=np.uint8)

        ret, frame = self._cap.read()
        if not ret:
            logger.warning("Failed to read frame from camera %d", self._device_id)
            return False, np.zeros((self._height, self._width, 3), dtype=np.uint8)

        # Mirror the frame so the user sees a natural reflection
        frame = cv2.flip(frame, 1)

        # Update FPS
        now = time.time()
        if self._last_frame_time > 0:
            elapsed = now - self._last_frame_time
            if elapsed > 0:
                self._fps = 1.0 / elapsed
        self._last_frame_time = now

        return True, frame

    def get_fps(self) -> float:
        """Return the real measured frames-per-second.

        Returns:
            Current FPS as a float (0.0 before first frame pair is read).
        """
        return self._fps

    def release(self) -> None:
        """Release the camera resource."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("Camera %d released", self._device_id)

    def __enter__(self) -> "CameraCapture":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
