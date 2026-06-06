"""Optional ML-based gesture classifier (Fase 3). Falls back gracefully when no model exists."""

import logging
import os
import pickle
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Default paths relative to project root
DEFAULT_MODEL_PATH = "models/gesture_v1.pkl"
DEFAULT_ENCODER_PATH = "models/label_encoder.pkl"


class GestureClassifier:
    """Random-Forest gesture classifier loaded from a .pkl file.

    Use GestureClassifier.get_instance() for a shared singleton.

    Args:
        model_path: Path to the trained RandomForest .pkl file.
        encoder_path: Path to the LabelEncoder .pkl file.
    """

    _instance: Optional["GestureClassifier"] = None

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH, encoder_path: str = DEFAULT_ENCODER_PATH) -> None:
        self._model = None
        self._encoder = None
        self._loaded = False

        if os.path.exists(model_path) and os.path.exists(encoder_path):
            try:
                with open(model_path, "rb") as f:
                    self._model = pickle.load(f)
                with open(encoder_path, "rb") as f:
                    self._encoder = pickle.load(f)
                self._loaded = True
                logger.info("ML classifier loaded from %s", model_path)
            except (pickle.UnpicklingError, EOFError, OSError) as exc:
                logger.warning("Failed to load ML classifier: %s", exc)
        else:
            logger.debug("No ML model found at %s — using rule-based fallback", model_path)

    @classmethod
    def get_instance(cls) -> Optional["GestureClassifier"]:
        """Return a shared singleton instance, creating it if needed.

        Returns:
            GestureClassifier singleton, or None if instantiation fails.
        """
        if cls._instance is None:
            try:
                cls._instance = cls()
            except Exception as exc:  # noqa: BLE001
                logger.error("Could not create GestureClassifier: %s", exc)
                return None
        return cls._instance

    def is_loaded(self) -> bool:
        """Check whether a model was successfully loaded.

        Returns:
            True if a trained model is available.
        """
        return self._loaded

    def predict(self, landmarks: list) -> tuple[str, float]:
        """Predict gesture from 21 hand landmarks.

        Normalizes landmarks relative to the wrist (landmark 0) before prediction.

        Args:
            landmarks: List of 21 NormalizedLandmark objects with .x, .y, .z attributes.

        Returns:
            Tuple of (gesture_name, probability).
        """
        if not self._loaded or self._model is None or self._encoder is None:
            return "desconocido", 0.0

        # Flatten and normalize relative to wrist
        wrist = landmarks[0]
        features: list[float] = []
        for lm in landmarks:
            features.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])

        X = np.array(features, dtype=np.float32).reshape(1, -1)
        proba = self._model.predict_proba(X)[0]
        class_idx = int(np.argmax(proba))
        confidence = float(proba[class_idx])
        label = self._encoder.inverse_transform([class_idx])[0]
        return str(label), confidence
