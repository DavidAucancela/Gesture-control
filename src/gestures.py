"""Rule-based gesture recognition from MediaPipe hand landmarks."""

import logging
import math
from dataclasses import dataclass

from src.detector import HandData

logger = logging.getLogger(__name__)

# Landmark index constants (mirrors detector.py without import cycle)
_WRIST = 0
_THUMB_CMC = 1
_THUMB_MCP = 2
_THUMB_IP = 3
_THUMB_TIP = 4
_INDEX_MCP = 5
_INDEX_PIP = 6
_INDEX_TIP = 8
_MIDDLE_PIP = 10
_MIDDLE_TIP = 12
_RING_PIP = 14
_RING_TIP = 16
_PINKY_PIP = 18
_PINKY_TIP = 20

# Distance threshold for OK gesture (normalized coordinates)
_OK_DISTANCE_THRESHOLD = 0.06


@dataclass
class GestureResult:
    """Result of gesture classification for a single hand.

    Attributes:
        name: Gesture name (e.g. 'victoria', 'punio', 'ok', 'señalar').
        confidence: Confidence score 0.0–1.0 (rule-based always returns 1.0).
        fingers_up: Boolean list [thumb, index, middle, ring, pinky].
        hand: 'Right' or 'Left'.
    """

    name: str
    confidence: float
    fingers_up: list[bool]
    hand: str


def _distance(p1, p2) -> float:
    """Compute Euclidean distance between two landmarks (x, y).

    Args:
        p1: Landmark with .x and .y attributes.
        p2: Landmark with .x and .y attributes.

    Returns:
        Euclidean distance as a float.
    """
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def _fingers_up(lm: list, handedness: str) -> list[bool]:
    """Determine which fingers are extended.

    Thumb is evaluated on the X axis (accounts for mirror flip).
    Fingers 2–5 are evaluated on the Y axis (tip.y < pip.y = extended).

    Args:
        lm: List of 21 NormalizedLandmark objects.
        handedness: 'Right' or 'Left' (user's perspective, post-flip).

    Returns:
        List of 5 booleans: [thumb, index, middle, ring, pinky].
    """
    fingers: list[bool] = []

    # Thumb: compare X positions (after horizontal flip)
    if handedness == "Right":
        fingers.append(lm[_THUMB_TIP].x < lm[_THUMB_IP].x)
    else:
        fingers.append(lm[_THUMB_TIP].x > lm[_THUMB_IP].x)

    # Index finger
    fingers.append(lm[_INDEX_TIP].y < lm[_INDEX_PIP].y)
    # Middle finger
    fingers.append(lm[_MIDDLE_TIP].y < lm[_MIDDLE_PIP].y)
    # Ring finger
    fingers.append(lm[_RING_TIP].y < lm[_RING_PIP].y)
    # Pinky finger
    fingers.append(lm[_PINKY_TIP].y < lm[_PINKY_PIP].y)

    return fingers


def _recognize_rule_based(lm: list, fingers: list[bool]) -> str:
    """Classify a gesture using deterministic rules.

    Args:
        lm: List of 21 NormalizedLandmark objects.
        fingers: Result of _fingers_up() — [thumb, index, middle, ring, pinky].

    Returns:
        Gesture name string.
    """
    thumb, index, middle, ring, pinky = fingers
    total_up = sum(fingers)

    if total_up == 0:
        return "punio"

    if total_up == 5:
        return "mano_abierta"

    # Thumb-only gestures
    if fingers == [True, False, False, False, False]:
        if lm[_THUMB_TIP].y < lm[_THUMB_MCP].y:
            return "pulgar_arriba"
        if lm[_THUMB_TIP].y > lm[_THUMB_CMC].y:
            return "pulgar_abajo"

    if fingers == [False, True, False, False, False]:
        return "señalar"

    if fingers == [False, True, True, False, False]:
        return "victoria"

    if fingers == [False, True, False, False, True]:
        return "rock"

    # OK: thumb tip close to index tip, remaining fingers up
    if not thumb and not index:
        if (
            _distance(lm[_THUMB_TIP], lm[_INDEX_TIP]) < _OK_DISTANCE_THRESHOLD
            and middle
            and ring
            and pinky
        ):
            return "ok"

    if fingers == [False, True, True, True, False]:
        return "tres"

    if fingers == [False, True, True, True, True]:
        return "cuatro"

    return "desconocido"


def recognize(hand: HandData) -> GestureResult:
    """Recognize the gesture performed by a single hand.

    Uses rule-based classification. If a trained ML classifier is available
    (src.classifier.GestureClassifier), it will be used instead as a drop-in
    replacement (transparent to callers).

    Args:
        hand: HandData with 21 landmarks and handedness label.

    Returns:
        GestureResult with name, confidence, fingers_up, and hand side.
    """
    lm = hand.landmarks
    fingers = _fingers_up(lm, hand.handedness)

    # Optional ML override (loaded lazily to avoid import errors when model missing)
    try:
        from src.classifier import GestureClassifier  # noqa: PLC0415

        clf = GestureClassifier.get_instance()
        if clf is not None and clf.is_loaded():
            gesture_name, confidence = clf.predict(lm)
            return GestureResult(
                name=gesture_name,
                confidence=confidence,
                fingers_up=fingers,
                hand=hand.handedness,
            )
    except ImportError:
        pass

    gesture_name = _recognize_rule_based(lm, fingers)
    return GestureResult(
        name=gesture_name,
        confidence=1.0,
        fingers_up=fingers,
        hand=hand.handedness,
    )
