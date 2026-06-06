"""Train a RandomForest gesture classifier from collected CSV data.

Usage:
    python tools/train.py

Output:
    models/gesture_v1.pkl
    models/label_encoder.pkl
"""

import glob
import logging
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def _normalize_landmarks(row: np.ndarray) -> np.ndarray:
    """Normalize 63 landmark features relative to wrist (landmark 0).

    Args:
        row: 1D array of 63 floats (21 landmarks * 3 axes).

    Returns:
        Normalized 1D array of 63 floats.
    """
    wrist = row[:3].copy()
    normalized = row.copy()
    for i in range(21):
        normalized[i * 3 : i * 3 + 3] -= wrist
    return normalized


def main() -> None:
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import classification_report

    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not csv_files:
        logger.error("No CSV files found in %s. Run tools/collect_data.py first.", DATA_DIR)
        sys.exit(1)

    dfs = []
    for path in csv_files:
        try:
            df = pd.read_csv(path)
            dfs.append(df)
            logger.info("Loaded %d samples from %s", len(df), path)
        except Exception as exc:
            logger.warning("Skipping %s: %s", path, exc)

    data = pd.concat(dfs, ignore_index=True)
    logger.info("Total samples: %d", len(data))

    feature_cols = [c for c in data.columns if c != "label"]
    X = data[feature_cols].values.astype(np.float32)
    y = data["label"].values

    # Normalize each sample
    X = np.apply_along_axis(_normalize_landmarks, 1, X)

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=le.classes_)
    logger.info("Classification report:\n%s", report)

    model_path = os.path.join(MODELS_DIR, "gesture_v1.pkl")
    encoder_path = os.path.join(MODELS_DIR, "label_encoder.pkl")

    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
    with open(encoder_path, "wb") as f:
        pickle.dump(le, f)

    logger.info("Model saved → %s", model_path)
    logger.info("Encoder saved → %s", encoder_path)


if __name__ == "__main__":
    main()
