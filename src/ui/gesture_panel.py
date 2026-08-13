"""Real-time gesture information panel."""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class GestureInfo:
    """Information about a detected gesture."""
    name: str
    hand: str  # "Right" or "Left"
    confidence: float  # 0.0 to 1.0
    hand_position: tuple[float, float]  # (x, y) normalized coordinates
    finger_states: list[bool]  # Which fingers are extended
    action_mapped: Optional[str] = None


class GesturePanel:
    """Displays gesture information and statistics."""

    def __init__(self) -> None:
        self._current_gestures: dict[str, GestureInfo] = {}
        self._gesture_history: list[str] = []
        self._max_history = 20

    def update(self, gestures: list[GestureInfo]) -> None:
        """Update panel with current gesture detections.

        Args:
            gestures: List of current gesture detections.
        """
        self._current_gestures.clear()
        for gesture in gestures:
            key = gesture.hand
            self._current_gestures[key] = gesture
            if gesture.name not in self._gesture_history:
                self._gesture_history.append(gesture.name)
                if len(self._gesture_history) > self._max_history:
                    self._gesture_history.pop(0)

    @property
    def current_gestures(self) -> dict[str, GestureInfo]:
        """Get currently detected gestures by hand."""
        return self._current_gestures

    @property
    def gesture_count(self) -> int:
        """Get number of hands with gestures."""
        return len(self._current_gestures)

    def get_gesture_info(self, hand: str) -> Optional[GestureInfo]:
        """Get gesture info for a specific hand.

        Args:
            hand: "Right" or "Left"

        Returns:
            GestureInfo or None if no gesture detected for that hand.
        """
        return self._current_gestures.get(hand)

    def format_gesture_display(self) -> str:
        """Format current gestures for display.

        Returns:
            String representation of current gestures.
        """
        if not self._current_gestures:
            return "No hands detected"

        lines = []
        for hand in ["Right", "Left"]:
            gesture = self._current_gestures.get(hand)
            if gesture:
                status = f"✓ {gesture.name.upper()}"
                if gesture.action_mapped:
                    status += f" → {gesture.action_mapped}"
                lines.append(f"{hand:5s}: {status}")
        return " | ".join(lines) if lines else "No hands detected"

    def format_detailed_info(self, hand: str) -> str:
        """Get detailed information for a specific hand.

        Args:
            hand: "Right" or "Left"

        Returns:
            Multi-line detailed information.
        """
        gesture = self._current_gestures.get(hand)
        if not gesture:
            return f"{hand} hand: Not detected"

        fingers = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        extended = [fingers[i] for i, state in enumerate(gesture.finger_states) if state]

        info = [
            f"Hand: {gesture.name.upper()}",
            f"Confidence: {gesture.confidence:.1%}",
            f"Position: ({gesture.hand_position[0]:.2f}, {gesture.hand_position[1]:.2f})",
            f"Fingers: {', '.join(extended) if extended else 'None'}",
        ]
        if gesture.action_mapped:
            info.append(f"Action: {gesture.action_mapped}")

        return "\n".join(info)
