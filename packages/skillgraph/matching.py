"""
Job matching algorithms using skill vectors.
"""

import numpy as np
from typing import Optional


def compute_job_fit(
    user_vector: list[float],
    job_vector: list[float],
) -> float:
    """
    Compute fit score between user and job using cosine similarity.

    Args:
        user_vector: User's skill vector
        job_vector: Job's target skill vector

    Returns:
        Fit score between 0 and 1
    """
    if not user_vector or not job_vector:
        return 0.0

    # Pad vectors to same length
    max_len = max(len(user_vector), len(job_vector))
    u = np.array(user_vector + [0.0] * (max_len - len(user_vector)))
    j = np.array(job_vector + [0.0] * (max_len - len(job_vector)))

    # Compute cosine similarity
    dot = np.dot(u, j)
    norm_u = np.linalg.norm(u)
    norm_j = np.linalg.norm(j)

    if norm_u == 0 or norm_j == 0:
        return 0.0

    similarity = dot / (norm_u * norm_j)

    # Clamp to 0-1 range
    return float(max(0.0, min(1.0, similarity)))


def compute_weighted_fit(
    user_vector: list[float],
    job_vector: list[float],
    weights: Optional[list[float]] = None,
) -> float:
    """
    Compute weighted fit score.

    Args:
        user_vector: User's skill vector
        job_vector: Job's target skill vector
        weights: Importance weights for each dimension

    Returns:
        Weighted fit score between 0 and 1
    """
    if not user_vector or not job_vector:
        return 0.0

    max_len = max(len(user_vector), len(job_vector))
    u = np.array(user_vector + [0.0] * (max_len - len(user_vector)))
    j = np.array(job_vector + [0.0] * (max_len - len(job_vector)))

    if weights is None:
        weights = [1.0] * max_len
    else:
        weights = weights + [1.0] * (max_len - len(weights))

    w = np.array(weights)

    # Weighted cosine similarity
    weighted_u = u * np.sqrt(w)
    weighted_j = j * np.sqrt(w)

    dot = np.dot(weighted_u, weighted_j)
    norm_u = np.linalg.norm(weighted_u)
    norm_j = np.linalg.norm(weighted_j)

    if norm_u == 0 or norm_j == 0:
        return 0.0

    similarity = dot / (norm_u * norm_j)
    return float(max(0.0, min(1.0, similarity)))


def rank_jobs(
    user_vector: list[float],
    jobs: list[dict],
) -> list[dict]:
    """
    Rank jobs by fit score for a user.

    Args:
        user_vector: User's skill vector
        jobs: List of job dictionaries with 'target_vector' field

    Returns:
        Jobs sorted by fit score (descending)
    """
    scored_jobs = []

    for job in jobs:
        job_vector = job.get("target_vector", [])
        fit_score = compute_job_fit(user_vector, job_vector)

        scored_job = {**job, "fit_score": round(fit_score, 3)}
        scored_jobs.append(scored_job)

    # Sort by fit score descending
    scored_jobs.sort(key=lambda j: j["fit_score"], reverse=True)

    return scored_jobs


def check_job_requirements(
    user_data: dict,
    job: dict,
) -> tuple[bool, list[str]]:
    """
    Check if user meets job requirements.

    Args:
        user_data: User data including passport info
        job: Job with 'must_have' requirements

    Returns:
        Tuple of (meets_requirements, list of missing requirements)
    """
    must_have = job.get("must_have", {})
    missing = []

    # Check minimum integrity
    if must_have.get("min_integrity"):
        user_integrity = user_data.get("metrics", {}).get("integrity", 0)
        if user_integrity < must_have["min_integrity"]:
            missing.append(f"integrity score of {must_have['min_integrity']}")

    # Check minimum sessions
    if must_have.get("min_sessions"):
        user_sessions = user_data.get("sessions_completed", 0)
        if user_sessions < must_have["min_sessions"]:
            missing.append(f"{must_have['min_sessions']} completed sessions")

    # Check required archetypes
    if must_have.get("required_archetypes"):
        user_archetype = user_data.get("archetype")
        if user_archetype not in must_have["required_archetypes"]:
            archetypes_str = " or ".join(must_have["required_archetypes"])
            missing.append(f"archetype: {archetypes_str}")

    return len(missing) == 0, missing
