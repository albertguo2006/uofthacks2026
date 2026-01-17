"""
Archetype clustering and prediction.
"""

import pickle
from pathlib import Path
from typing import Optional
import numpy as np


MODELS_DIR = Path(__file__).parent / "models"

# Archetype definitions for rule-based fallback
ARCHETYPE_CENTERS = {
    "fast_iterator": [0.8, 0.5, 0.4, 0.7, 0.8],
    "careful_tester": [0.4, 0.7, 0.8, 0.5, 0.95],
    "debugger": [0.6, 0.85, 0.5, 0.6, 0.85],
    "craftsman": [0.5, 0.6, 0.85, 0.7, 0.9],
    "explorer": [0.7, 0.5, 0.5, 0.5, 0.75],
}


def load_models():
    """Load trained models from disk."""
    try:
        kmeans_path = MODELS_DIR / "kmeans.pkl"
        scaler_path = MODELS_DIR / "scaler.pkl"
        mapping_path = MODELS_DIR / "cluster_mapping.pkl"

        if not all(p.exists() for p in [kmeans_path, scaler_path, mapping_path]):
            return None, None, None

        with open(kmeans_path, "rb") as f:
            kmeans = pickle.load(f)
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)
        with open(mapping_path, "rb") as f:
            cluster_mapping = pickle.load(f)

        return kmeans, scaler, cluster_mapping
    except Exception:
        return None, None, None


def predict_archetype_ml(skill_vector: list[float]) -> tuple[str, float]:
    """Predict archetype using trained ML model."""
    kmeans, scaler, cluster_mapping = load_models()

    if kmeans is None:
        return None, 0.0

    try:
        scaled = scaler.transform([skill_vector])
        cluster = kmeans.predict(scaled)[0]
        archetype = cluster_mapping[cluster]

        # Compute confidence based on distance to centroid
        centroid = kmeans.cluster_centers_[cluster]
        distance = np.linalg.norm(scaled[0] - centroid)
        confidence = max(0.0, 1.0 - (distance / 2.0))  # Normalize

        return archetype, round(confidence, 3)
    except Exception:
        return None, 0.0


def predict_archetype_rules(skill_vector: list[float]) -> tuple[str, float]:
    """Predict archetype using rule-based approach (fallback)."""
    if not skill_vector or len(skill_vector) < 5:
        return None, 0.0

    # Compute weighted scores for each archetype
    scores = {}

    iteration_velocity = skill_vector[0]
    debug_efficiency = skill_vector[1]
    craftsmanship = skill_vector[2]
    tool_fluency = skill_vector[3]
    integrity = skill_vector[4]

    scores["fast_iterator"] = (
        iteration_velocity * 0.5 +
        tool_fluency * 0.3 +
        debug_efficiency * 0.2
    )

    scores["careful_tester"] = (
        craftsmanship * 0.4 +
        debug_efficiency * 0.4 +
        integrity * 0.2
    )

    scores["debugger"] = (
        debug_efficiency * 0.5 +
        iteration_velocity * 0.3 +
        tool_fluency * 0.2
    )

    scores["craftsman"] = (
        craftsmanship * 0.5 +
        integrity * 0.3 +
        debug_efficiency * 0.2
    )

    scores["explorer"] = (
        iteration_velocity * 0.4 +
        debug_efficiency * 0.3 +
        craftsmanship * 0.3
    )

    best_archetype = max(scores, key=scores.get)
    confidence = scores[best_archetype]

    return best_archetype, round(confidence, 3)


def predict_archetype(skill_vector: list[float]) -> tuple[str, float]:
    """
    Predict archetype from skill vector.
    Uses ML model if available, falls back to rules.
    """
    # Try ML model first
    archetype, confidence = predict_archetype_ml(skill_vector)

    if archetype:
        return archetype, confidence

    # Fallback to rules
    return predict_archetype_rules(skill_vector)
