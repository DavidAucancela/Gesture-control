"""MediaPipe Hands wrapper providing structured hand landmark data."""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import mediapipe as mp
import numpy as np

logger = logging.getLogger(__name__)

# MediaPipe landmark index constants
LM_WRIST = 0
LM_THUMB_CMC = 1
LM_THUMB_MCP = 2
LM_THUMB_IP = 3
LM_THUMB_TIP = 4
LM_INDEX_MCP = 5
LM_INDEX_PIP = 6
LM_INDEX_DIP = 7
LM_INDEX_TIP = 8
LM_MIDDLE_MCP = 9
LM_MIDDLE_PIP = 10
LM_MIDDLE_DIP = 11
LM_MIDDLE_TIP = 12
LM_RING_MCP = 13
LM_RING_PIP = 14
LM_RING_DIP = 15
LM_RING_TIP = 16
LM_PINKY_MCP = 17
LM_PINKY_PIP = 18
LM_PINKY_DIP = 19
LM_PINKY_TIP = 20


@dataclass
class HandData:
    """Structured data for a single detected hand.

    Attributes:
        landmarks: List of 21 NormalizedLandmark objects (x, y, z in [0,1]).
        handedness: 'Right' or 'Left' from the user's perspective.
        world_landmarks: List of 21 landmarks in metric 3D coordinates.
    """

    landmarks: list
    handedness: str
    world_landmarks: list


@dataclass
class DetectionResult:
    """Result of a single frame's hand detection.

    Attributes:
        hands: List of HandData (0, 1 or 2 entries).
        raw_result: Raw MediaPipe result object (used for drawing).
    """

    hands: list[HandData] = field(default_factory=list)
    raw_result: Any = None


class HandDetector:
    """Wrapper around MediaPipe Hands for structured landmark detection.

    Args:
        max_hands: Maximum number of hands to detect (1 or 2).
        min_detection_conf: Minimum confidence threshold for initial detection.
        min_tracking_conf: Minimum confidence threshold for tracking.
    """

    def __init__(
        self,
        max_hands: int = 2,
        min_detection_conf: float = 0.75,
        min_tracking_conf: float = 0.65,
    ) -> None:
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=min_detection_conf,
            min_tracking_confidence=min_tracking_conf,
        )
        logger.info(
            "HandDetector initialized (max_hands=%d, det_conf=%.2f, track_conf=%.2f)",
            max_hands,
            min_detection_conf,
            min_tracking_conf,
        )

    def detect(self, frame_rgb: np.ndarray) -> DetectionResult:
        """Detect hands in an RGB frame.

        Args:
            frame_rgb: numpy array in RGB format (H x W x 3).

        Returns:
            DetectionResult containing all detected hands.
        """
        result = self._hands.process(frame_rgb)
        hands: list[HandData] = []

        if result.multi_hand_landmarks:
            for idx, hand_lm in enumerate(result.multi_hand_landmarks):
                handedness_label = "Right"
                if result.multi_handedness and idx < len(result.multi_handedness):
                    handedness_label = result.multi_handedness[idx].classification[0].label

                world_lm = []
                if result.multi_hand_world_landmarks and idx < len(
                    result.multi_hand_world_landmarks
                ):
                    world_lm = list(result.multi_hand_world_landmarks[idx].landmark)

                hands.append(
                    HandData(
                        landmarks=list(hand_lm.landmark),
                        handedness=handedness_label,
                        world_landmarks=world_lm,
                    )
                )

        return DetectionResult(hands=hands, raw_result=result)

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._hands.close()
        logger.info("HandDetector closed")

    def __enter__(self) -> "HandDetector":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
