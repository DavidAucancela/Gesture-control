"""Camera selection and control interface."""

import cv2
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class CameraSelector:
    """Manages available cameras and current selection."""

    def __init__(self, default_device_id: int = 0) -> None:
        self._cameras = self._detect_cameras()
        self._current_device_id = default_device_id
        logger.info(f"Found {len(self._cameras)} camera(s): {self._cameras}")

    @staticmethod
    def _detect_cameras(max_index: int = 10) -> list[int]:
        """Detect available cameras by trying to open them."""
        available = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available

    @property
    def available_cameras(self) -> list[int]:
        """Get list of available camera indices."""
        return self._cameras

    @property
    def current_device_id(self) -> int:
        """Get current camera device ID."""
        return self._current_device_id

    def switch_camera(self, device_id: int) -> bool:
        """Switch to a different camera.

        Args:
            device_id: Camera device index to switch to.

        Returns:
            True if camera is available, False otherwise.
        """
        if device_id in self._cameras:
            self._current_device_id = device_id
            logger.info(f"Switched to camera {device_id}")
            return True
        logger.warning(f"Camera {device_id} not available")
        return False

    def refresh_cameras(self) -> None:
        """Re-detect available cameras."""
        self._cameras = self._detect_cameras()
        logger.info(f"Refreshed camera list: {self._cameras}")
        if self._current_device_id not in self._cameras and self._cameras:
            self._current_device_id = self._cameras[0]
            logger.warning(f"Current camera not available, switched to {self._current_device_id}")

    def get_camera_name(self, device_id: int) -> str:
        """Get user-friendly name for camera."""
        names = {
            0: "Laptop Camera",
            1: "External Camera / Phone",
            2: "USB Camera",
        }
        return names.get(device_id, f"Camera {device_id}")
