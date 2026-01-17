#!/usr/bin/env python3
"""
Train and export ML models for archetype classification.
Usage: python scripts/train_models.py
"""

import asyncio
import os
import pickle
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from motor.motor_asyncio import AsyncIOMotorClient


MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "proof_of_skill")
MODELS_DIR = Path(__file__).parent.parent / "packages" / "skillgraph" / "models"


# Archetype centers (manually defined based on expected characteristics)
# [iteration_velocity, debug_efficiency, craftsmanship, tool_fluency, integrity]
ARCHETYPE_CENTERS = {
    "fast_iterator": [0.8, 0.5, 0.4, 0.7, 0.8],
    "careful_tester": [0.4, 0.7, 0.8, 0.5, 0.95],
    "debugger": [0.6, 0.85, 0.5, 0.6, 0.85],
    "craftsman": [0.5, 0.6, 0.85, 0.7, 0.9],
    "explorer": [0.7, 0.5, 0.5, 0.5, 0.75],
}


def generate_synthetic_data(n_samples_per_archetype: int = 100):
    """Generate synthetic training data based on archetype centers."""
    X = []
    y = []

    for archetype, center in ARCHETYPE_CENTERS.items():
        # Generate samples around each center with some noise
        for _ in range(n_samples_per_archetype):
            sample = [
                np.clip(c + np.random.normal(0, 0.15), 0, 1)
                for c in center
            ]
            X.append(sample)
            y.append(archetype)

    return np.array(X), y


def train_kmeans_model():
    """Train KMeans model for archetype clustering."""
    print("Generating synthetic training data...")
    X, y = generate_synthetic_data(100)

    print(f"Training data shape: {X.shape}")

    # Train scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train KMeans with 5 clusters (one per archetype)
    print("Training KMeans model...")
    kmeans = KMeans(
        n_clusters=5,
        init="k-means++",
        n_init=10,
        max_iter=300,
        random_state=42,
    )
    kmeans.fit(X_scaled)

    # Map cluster indices to archetype names based on centroids
    archetype_names = list(ARCHETYPE_CENTERS.keys())
    cluster_to_archetype = {}

    for cluster_idx in range(5):
        # Find closest archetype center
        cluster_center = scaler.inverse_transform(kmeans.cluster_centers_[cluster_idx:cluster_idx+1])[0]
        min_dist = float("inf")
        best_archetype = None

        for archetype, center in ARCHETYPE_CENTERS.items():
            if archetype in cluster_to_archetype.values():
                continue
            dist = np.linalg.norm(np.array(center) - cluster_center)
            if dist < min_dist:
                min_dist = dist
                best_archetype = archetype

        cluster_to_archetype[cluster_idx] = best_archetype

    print(f"Cluster mapping: {cluster_to_archetype}")

    return kmeans, scaler, cluster_to_archetype


def save_models(kmeans, scaler, cluster_mapping):
    """Save trained models to disk."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    kmeans_path = MODELS_DIR / "kmeans.pkl"
    scaler_path = MODELS_DIR / "scaler.pkl"
    mapping_path = MODELS_DIR / "cluster_mapping.pkl"

    with open(kmeans_path, "wb") as f:
        pickle.dump(kmeans, f)
    print(f"Saved KMeans model to: {kmeans_path}")

    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"Saved scaler to: {scaler_path}")

    with open(mapping_path, "wb") as f:
        pickle.dump(cluster_mapping, f)
    print(f"Saved cluster mapping to: {mapping_path}")


def test_model(kmeans, scaler, cluster_mapping):
    """Test the trained model with sample predictions."""
    print("\nTesting model predictions:")

    test_cases = [
        ("High iterator", [0.9, 0.5, 0.3, 0.8, 0.85]),
        ("Careful tester", [0.3, 0.8, 0.85, 0.4, 0.98]),
        ("Debugger", [0.5, 0.9, 0.5, 0.6, 0.88]),
        ("Craftsman", [0.4, 0.6, 0.9, 0.75, 0.92]),
        ("Explorer", [0.75, 0.45, 0.45, 0.5, 0.7]),
    ]

    for name, vector in test_cases:
        scaled = scaler.transform([vector])
        cluster = kmeans.predict(scaled)[0]
        archetype = cluster_mapping[cluster]
        print(f"  {name}: predicted '{archetype}'")


def main():
    print("=== Training Archetype Classification Model ===\n")

    # Train model
    kmeans, scaler, cluster_mapping = train_kmeans_model()

    # Test model
    test_model(kmeans, scaler, cluster_mapping)

    # Save models
    print("\n=== Saving Models ===")
    save_models(kmeans, scaler, cluster_mapping)

    print("\n=== Training Complete ===")


if __name__ == "__main__":
    main()
