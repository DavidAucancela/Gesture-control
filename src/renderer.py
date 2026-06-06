"""Overlay renderer: draws landmarks, gesture labels, FPS, and status bar."""

import logging
import time
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

from src.detector import DetectionResult
from src.gestures import GestureResult

logger = logging.getLogger(__name__)

# Drawing utilities from MediaPipe
_MP_DRAWING = mp.solutions.drawing_utils
_MP_HANDS = mp.solutions.hands

# Visual constants
_FPS_COLOR = (0, 255, 0)          # Green
_LABEL_BG_COLOR = (30, 30, 30)    # Dark grey
_LABEL_TEXT_COLOR = (255, 255, 255)  # White
_STATUS_BG_COLOR = (20, 20, 20)   # Near-black
_STATUS_TEXT_COLOR = (200, 200, 200)
_TOAST_BG_COLOR = (20, 20, 20)    # Dark
_TOAST_TEXT_COLOR = (0, 230, 255) # Cyan
_TOAST_TTL = 1.8                  # seconds before toast disappears
_TOAST_FADE_START = 0.5           # seconds before end to start fading
_FONT = cv2.FONT_HERSHEY_SIMPLEX

_ACTION_LABELS = {
    "mano_abierta": "Mano abierta",
    "punio": "Punio",
    "señalar": "Señalar",
    "victoria": "Victoria",
    "rock": "Rock",
    "pulgar_arriba": "Pulgar arriba",
    "pulgar_abajo": "Pulgar abajo",
    "ok": "OK",
}

def _format_action(action_str: str) -> str:
    if ":" not in action_str:
        return action_str
    action_type, payload = action_str.split(":", 1)
    if action_type == "key_press":
        return payload.upper()
    if action_type == "mouse_click":
        return f"Click {payload}"
    if action_type == "mouse_scroll":
        direction = payload.split(":")[0]
        return f"Scroll {direction}"
    return action_str


class Renderer:
    """Renders hand landmarks, gesture labels, FPS, and UI overlays.

    Args:
        settings: Dictionary from the 'renderer' section of settings.yaml.
    """

    def __init__(self, settings: dict) -> None:
        self._show_landmarks: bool = settings.get("show_landmarks", True)
        self._show_fps: bool = settings.get("show_fps", True)
        self._show_gesture_label: bool = settings.get("show_gesture_label", True)
        self._font_scale: float = float(settings.get("font_scale", 0.9))
        self._overlay_alpha: float = float(settings.get("overlay_alpha", 0.55))
        self._toast_label: str = ""
        self._toast_ts: float = 0.0

    def notify_action(self, gesture_name: str, action_str: str) -> None:
        gesture_display = _ACTION_LABELS.get(gesture_name, gesture_name)
        action_display = _format_action(action_str)
        self._toast_label = f"{gesture_display}  ->  {action_display}"
        self._toast_ts = time.monotonic()

    def draw(
        self,
        frame: np.ndarray,
        detection_result: DetectionResult,
        gesture_results: list[GestureResult],
        fps: float,
    ) -> np.ndarray:
        """Compose all visual overlays onto the frame.

        Args:
            frame: BGR numpy array from the camera.
            detection_result: DetectionResult from HandDetector.
            gesture_results: List of GestureResult, one per detected hand.
            fps: Current frames-per-second measurement.

        Returns:
            Annotated BGR numpy array.
        """
        output = frame.copy()

        # Draw MediaPipe hand skeleton
        if self._show_landmarks and detection_result.raw_result.multi_hand_landmarks:
            for hand_lm in detection_result.raw_result.multi_hand_landmarks:
                _MP_DRAWING.draw_landmarks(
                    output,
                    hand_lm,
                    _MP_HANDS.HAND_CONNECTIONS,
                    _MP_DRAWING.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                    _MP_DRAWING.DrawingSpec(color=(250, 44, 250), thickness=2),
                )

        # Draw gesture label per hand
        if self._show_gesture_label and detection_result.raw_result.multi_hand_landmarks:
            h, w = output.shape[:2]
            for idx, (hand_lm, gesture) in enumerate(
                zip(detection_result.raw_result.multi_hand_landmarks, gesture_results)
            ):
                # Compute bounding box for hand
                xs = [lm.x * w for lm in hand_lm.landmark]
                ys = [lm.y * h for lm in hand_lm.landmark]
                x_min = max(int(min(xs)) - 10, 0)
                y_min = max(int(min(ys)) - 40, 0)

                label = f"{gesture.name} ({gesture.hand[0]})"
                output = self._draw_overlay(output, label, (x_min, y_min), _LABEL_BG_COLOR)

        # FPS counter
        if self._show_fps:
            fps_text = f"FPS: {fps:.1f}"
            output = self._draw_overlay(output, fps_text, (10, 30), _LABEL_BG_COLOR)

        # Action toast
        output = self._draw_action_toast(output)

        # Status bar at the bottom
        status_text = "Q: salir  |  R: resetear"
        output = self._draw_status_bar(output, status_text)

        return output

    def _draw_overlay(
        self,
        frame: np.ndarray,
        text: str,
        position: tuple[int, int],
        bg_color: tuple[int, int, int],
    ) -> np.ndarray:
        """Draw text with a semi-transparent background rectangle.

        Args:
            frame: BGR numpy array to draw on.
            text: String to render.
            position: (x, y) top-left corner of the text.
            bg_color: Background color as (B, G, R).

        Returns:
            Modified numpy array.
        """
        x, y = position
        (text_w, text_h), baseline = cv2.getTextSize(text, _FONT, self._font_scale, 2)
        padding = 6

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (x - padding, y - text_h - padding),
            (x + text_w + padding, y + baseline + padding),
            bg_color,
            -1,
        )
        cv2.addWeighted(overlay, self._overlay_alpha, frame, 1 - self._overlay_alpha, 0, frame)
        cv2.putText(frame, text, (x, y), _FONT, self._font_scale, _LABEL_TEXT_COLOR, 2)
        return frame

    def _draw_action_toast(self, frame: np.ndarray) -> np.ndarray:
        if not self._toast_label:
            return frame
        elapsed = time.monotonic() - self._toast_ts
        if elapsed > _TOAST_TTL:
            return frame

        # Fade out in the last _TOAST_FADE_START seconds
        remaining = _TOAST_TTL - elapsed
        alpha = min(1.0, remaining / _TOAST_FADE_START)

        h, w = frame.shape[:2]
        font_scale = self._font_scale * 1.1
        thickness = 2
        (tw, th), baseline = cv2.getTextSize(self._toast_label, _FONT, font_scale, thickness)
        padding = 14
        box_w = tw + padding * 2
        box_h = th + baseline + padding * 2
        x = (w - box_w) // 2
        y = h - 75  # above status bar

        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + box_w, y + box_h), _TOAST_BG_COLOR, -1)
        cv2.addWeighted(overlay, alpha * 0.85, frame, 1 - alpha * 0.85, 0, frame)

        text_color = tuple(int(c * alpha) for c in _TOAST_TEXT_COLOR)
        cv2.putText(
            frame,
            self._toast_label,
            (x + padding, y + padding + th),
            _FONT,
            font_scale,
            text_color,
            thickness,
        )
        return frame

    def _draw_status_bar(self, frame: np.ndarray, text: str) -> np.ndarray:
        """Draw a full-width status bar at the bottom of the frame.

        Args:
            frame: BGR numpy array to draw on.
            text: Status message to display.

        Returns:
            Modified numpy array.
        """
        h, w = frame.shape[:2]
        bar_height = 30
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - bar_height), (w, h), _STATUS_BG_COLOR, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        cv2.putText(
            frame,
            text,
            (10, h - 8),
            _FONT,
            0.55,
            _STATUS_TEXT_COLOR,
            1,
        )
        return frame
