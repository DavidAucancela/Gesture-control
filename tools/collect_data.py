"""Interactive landmark data collection tool for training the ML classifier.

Usage:
    python tools/collect_data.py

Controls:
    SPACE  — record current landmarks as a sample for the active gesture
    N      — advance to the next gesture in the list
    Q      — save and quit
"""

import csv
import logging
import os
import sys

import cv2
import mediapipe as mp
import yaml

# Ensure src is importable from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.capture import CameraCapture
from src.detector import HandDetector, HandData

_MP_DRAWING = mp.solutions.drawing_utils
_MP_HANDS = mp.solutions.hands

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

GESTURE_LIST = [
    "punio",
    "mano_abierta",
    "señalar",
    "victoria",
    "ok",
    "rock",
    "pulgar_arriba",
    "pulgar_abajo",
]

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(DATA_DIR, exist_ok=True)


def _flatten_landmarks(hand: HandData) -> list[float]:
    """Flatten 21 landmarks into a flat list of [x,y,z]*21."""
    features: list[float] = []
    for lm in hand.landmarks:
        features.extend([lm.x, lm.y, lm.z])
    return features


def main() -> None:
    gesture_idx = 0
    sample_count = 0
    rows: list[list] = []

    try:
        settings_path = os.path.join(os.path.dirname(__file__), "..", "config", "settings.yaml")
        with open(settings_path) as f:
            settings = yaml.safe_load(f)
        cam_cfg = settings["camera"]
        mp_cfg = settings["mediapipe"]
    except (FileNotFoundError, KeyError) as exc:
        logger.error("Cannot load settings: %s", exc)
        sys.exit(1)

    with CameraCapture(
        cam_cfg["device_id"],
        cam_cfg["width"],
        cam_cfg["height"],
        backend=cam_cfg.get("backend", "dshow"),
    ) as cap:
        with HandDetector(
            max_hands=1,
            min_detection_conf=mp_cfg["min_detection_confidence"],
            min_tracking_conf=mp_cfg["min_tracking_confidence"],
        ) as detector:

            logger.info("Data collection started. SPACE=record, N=next gesture, Q=quit")

            while gesture_idx < len(GESTURE_LIST):
                current_gesture = GESTURE_LIST[gesture_idx]
                ret, frame = cap.read()
                if not ret:
                    break

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detection = detector.detect(rgb)

                # HUD
                info = f"Gesto: {current_gesture}  |  Muestras: {sample_count}"
                cv2.putText(frame, info, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    "SPACE=grabar  N=siguiente  Q=salir",
                    (10, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (200, 200, 200),
                    1,
                )

                if detection.hands and detection.raw_result.multi_hand_landmarks:
                    _MP_DRAWING.draw_landmarks(
                        frame,
                        detection.raw_result.multi_hand_landmarks[0],
                        _MP_HANDS.HAND_CONNECTIONS,
                    )

                cv2.imshow("Gesture Control - Data Collection", frame)
                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    break
                elif key == ord("n"):
                    # Save current gesture data
                    _save_gesture_csv(current_gesture, rows, DATA_DIR)
                    rows = []
                    sample_count = 0
                    gesture_idx += 1
                    if gesture_idx < len(GESTURE_LIST):
                        logger.info("Next gesture: %s", GESTURE_LIST[gesture_idx])
                elif key == ord(" "):
                    if detection.hands:
                        features = _flatten_landmarks(detection.hands[0])
                        features.append(current_gesture)
                        rows.append(features)
                        sample_count += 1
                        logger.info("[%s] Sample #%d recorded", current_gesture, sample_count)
                    else:
                        logger.warning("No hand detected — sample skipped")

    # Save remaining
    if rows and gesture_idx < len(GESTURE_LIST):
        _save_gesture_csv(GESTURE_LIST[gesture_idx], rows, DATA_DIR)

    cv2.destroyAllWindows()
    logger.info("Data collection complete.")


def _save_gesture_csv(gesture_name: str, rows: list, data_dir: str) -> None:
    if not rows:
        return
    csv_path = os.path.join(data_dir, f"{gesture_name}.csv")
    header = [f"lm{i}_{axis}" for i in range(21) for axis in ("x", "y", "z")] + ["label"]
    mode = "a" if os.path.exists(csv_path) else "w"
    with open(csv_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if mode == "w":
            writer.writerow(header)
        writer.writerows(rows)
    logger.info("Saved %d samples for '%s' → %s", len(rows), gesture_name, csv_path)


if __name__ == "__main__":
    main()
