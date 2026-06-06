"""Unit tests for gesture recognition using mocked landmarks."""

import pytest
from dataclasses import dataclass

from src.gestures import recognize, _fingers_up, _distance
from src.detector import HandData


@dataclass
class MockLandmark:
    """Minimal landmark mock with x, y, z attributes."""
    x: float
    y: float
    z: float = 0.0


def make_landmark(x: float, y: float, z: float = 0.0) -> MockLandmark:
    """Create a mock landmark with the given coordinates.

    Args:
        x: Normalized x coordinate.
        y: Normalized y coordinate.
        z: Normalized z coordinate.

    Returns:
        MockLandmark instance.
    """
    return MockLandmark(x=x, y=y, z=z)


def _make_hand(landmarks: list, handedness: str = "Right") -> HandData:
    """Build a HandData with the given landmarks.

    Args:
        landmarks: List of 21 MockLandmark objects.
        handedness: 'Right' or 'Left'.

    Returns:
        HandData instance.
    """
    return HandData(landmarks=landmarks, handedness=handedness, world_landmarks=[])


def _make_default_landmarks() -> list:
    """Create 21 landmarks with all fingers closed (fist-like position).

    Returns:
        List of 21 MockLandmark objects.
    """
    # All landmarks stacked at same position — fingers bent
    lms = [make_landmark(0.5, 0.8) for _ in range(21)]

    # MediaPipe indices:
    # 0=WRIST, 1=THUMB_CMC, 2=THUMB_MCP, 3=THUMB_IP, 4=THUMB_TIP
    # 5=INDEX_MCP, 6=INDEX_PIP, 7=INDEX_DIP, 8=INDEX_TIP
    # 9=MIDDLE_MCP, 10=MIDDLE_PIP, 11=MIDDLE_DIP, 12=MIDDLE_TIP
    # 13=RING_MCP, 14=RING_PIP, 15=RING_DIP, 16=RING_TIP
    # 17=PINKY_MCP, 18=PINKY_PIP, 19=PINKY_DIP, 20=PINKY_TIP

    # Wrist at bottom center
    lms[0] = make_landmark(0.5, 0.9)

    # Thumb (all bent — tip x > ip x for Right hand = not extended)
    lms[1] = make_landmark(0.45, 0.82)  # CMC
    lms[2] = make_landmark(0.42, 0.78)  # MCP
    lms[3] = make_landmark(0.40, 0.75)  # IP
    lms[4] = make_landmark(0.42, 0.73)  # TIP (x > ip.x for right = not extended)

    # Index (bent — tip.y > pip.y)
    lms[5] = make_landmark(0.50, 0.70)  # MCP
    lms[6] = make_landmark(0.50, 0.65)  # PIP
    lms[7] = make_landmark(0.50, 0.68)  # DIP
    lms[8] = make_landmark(0.50, 0.70)  # TIP (y > pip.y = bent)

    # Middle (bent)
    lms[9]  = make_landmark(0.52, 0.70)
    lms[10] = make_landmark(0.52, 0.65)  # PIP
    lms[11] = make_landmark(0.52, 0.68)
    lms[12] = make_landmark(0.52, 0.70)  # TIP (bent)

    # Ring (bent)
    lms[13] = make_landmark(0.54, 0.70)
    lms[14] = make_landmark(0.54, 0.65)  # PIP
    lms[15] = make_landmark(0.54, 0.68)
    lms[16] = make_landmark(0.54, 0.70)  # TIP (bent)

    # Pinky (bent)
    lms[17] = make_landmark(0.56, 0.72)
    lms[18] = make_landmark(0.56, 0.68)  # PIP
    lms[19] = make_landmark(0.56, 0.70)
    lms[20] = make_landmark(0.56, 0.72)  # TIP (bent)

    return lms


def _extend_finger(lms: list, tip_idx: int, pip_idx: int) -> list:
    """Modify landmarks so the given finger is extended (tip above pip)."""
    lms = list(lms)
    pip = lms[pip_idx]
    lms[tip_idx] = make_landmark(pip.x, pip.y - 0.12)  # tip higher than pip
    return lms


def test_punio_quando_todos_dedos_bajos():
    """All fingers bent should produce 'punio'."""
    lms = _make_default_landmarks()
    hand = _make_hand(lms, "Right")
    result = recognize(hand)
    assert result.name == "punio"
    assert result.fingers_up == [False, False, False, False, False]


def test_mano_abierta_quando_todos_arriba():
    """All fingers extended should produce 'mano_abierta'."""
    lms = _make_default_landmarks()
    # Extend all 4 fingers
    lms = _extend_finger(lms, 8, 6)    # index
    lms = _extend_finger(lms, 12, 10)  # middle
    lms = _extend_finger(lms, 16, 14)  # ring
    lms = _extend_finger(lms, 20, 18)  # pinky
    # Extend thumb (Right hand: tip.x < ip.x)
    lms[4] = make_landmark(lms[3].x - 0.05, lms[3].y)
    hand = _make_hand(lms, "Right")
    result = recognize(hand)
    assert result.name == "mano_abierta"
    assert all(result.fingers_up)


def test_señalar_quando_solo_indice():
    """Only index finger extended should produce 'señalar'."""
    lms = _make_default_landmarks()
    lms = _extend_finger(lms, 8, 6)  # extend index
    hand = _make_hand(lms, "Right")
    result = recognize(hand)
    assert result.name == "señalar"
    assert result.fingers_up == [False, True, False, False, False]


def test_victoria_indice_y_medio():
    """Index and middle fingers extended should produce 'victoria'."""
    lms = _make_default_landmarks()
    lms = _extend_finger(lms, 8, 6)    # index
    lms = _extend_finger(lms, 12, 10)  # middle
    hand = _make_hand(lms, "Right")
    result = recognize(hand)
    assert result.name == "victoria"
    assert result.fingers_up == [False, True, True, False, False]


def test_pulgar_right_hand():
    """Thumb detection for Right hand should use X axis comparison."""
    lms = _make_default_landmarks()
    # For Right hand: thumb extended = tip.x < ip.x
    lms[4] = make_landmark(lms[3].x - 0.08, lms[3].y)
    hand = _make_hand(lms, "Right")
    fingers = _fingers_up(lms, "Right")
    assert fingers[0] is True, "Right hand thumb should be extended when tip.x < ip.x"


def test_desconocido_patron_invalido():
    """A pattern that matches no rule should return 'desconocido'."""
    lms = _make_default_landmarks()
    # Extend ring and pinky only — no matching gesture
    lms = _extend_finger(lms, 16, 14)  # ring
    lms = _extend_finger(lms, 20, 18)  # pinky
    hand = _make_hand(lms, "Right")
    result = recognize(hand)
    assert result.name == "desconocido"


def test_distance_helper():
    """_distance should compute correct Euclidean distance."""
    p1 = make_landmark(0.0, 0.0)
    p2 = make_landmark(0.03, 0.04)
    assert abs(_distance(p1, p2) - 0.05) < 1e-6
