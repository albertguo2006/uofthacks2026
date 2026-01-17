"""
Feature extraction from behavioral events.
"""

from typing import Any
import numpy as np


def extract_features(events: list[dict]) -> dict:
    """
    Extract features from a list of behavioral events.

    Features:
    - iteration_velocity: How quickly the user iterates (runs per minute)
    - debug_efficiency: Ratio of fixes to errors
    - craftsmanship: Clean code indicators (formatting, low error rate)
    - tool_fluency: Keyboard shortcut usage ratio
    - integrity: Inverse of suspicious activity (paste bursts)
    """
    if not events:
        return {}

    features = {
        "total_events": len(events),
        "run_attempts": 0,
        "errors_encountered": 0,
        "fixes_applied": 0,
        "commands_used": set(),
        "code_changes": 0,
        "paste_bursts": 0,
        "shortcut_commands": 0,
        "total_commands": 0,
    }

    for event in events:
        event_type = event.get("event_type", "")
        props = event.get("properties", {})

        if event_type == "run_attempted":
            features["run_attempts"] += 1

        elif event_type == "error_emitted":
            features["errors_encountered"] += 1

        elif event_type == "fix_applied":
            features["fixes_applied"] += 1

        elif event_type == "editor_command":
            features["commands_used"].add(props.get("command", ""))
            features["total_commands"] += 1
            if props.get("source") == "shortcut":
                features["shortcut_commands"] += 1

        elif event_type == "code_changed":
            features["code_changes"] += 1

        elif event_type == "paste_burst_detected":
            features["paste_bursts"] += 1

    return features


def compute_skill_vector(features: dict) -> list[float]:
    """
    Compute a 5-dimensional skill vector from extracted features.

    Dimensions:
    [iteration_velocity, debug_efficiency, craftsmanship, tool_fluency, integrity]
    """
    if not features:
        return [0.0, 0.0, 0.0, 0.0, 1.0]

    # Iteration velocity: runs normalized by expected range
    iteration_velocity = min(1.0, features.get("run_attempts", 0) / 15.0)

    # Debug efficiency: fixes per error
    errors = features.get("errors_encountered", 0)
    fixes = features.get("fixes_applied", 0)
    if errors > 0:
        debug_efficiency = min(1.0, fixes / errors)
    else:
        debug_efficiency = 1.0 if features.get("run_attempts", 0) > 0 else 0.0

    # Craftsmanship: inverse of error rate
    total_runs = features.get("run_attempts", 1)
    error_rate = errors / max(total_runs, 1)
    craftsmanship = max(0.0, 1.0 - error_rate)

    # Tool fluency: shortcut usage ratio
    total_commands = features.get("total_commands", 0)
    if total_commands > 0:
        tool_fluency = features.get("shortcut_commands", 0) / total_commands
    else:
        tool_fluency = 0.5

    # Integrity: penalize paste bursts
    paste_bursts = features.get("paste_bursts", 0)
    integrity = max(0.0, 1.0 - (paste_bursts / 5.0))

    return [
        round(iteration_velocity, 3),
        round(debug_efficiency, 3),
        round(craftsmanship, 3),
        round(tool_fluency, 3),
        round(integrity, 3),
    ]


def aggregate_vectors(vectors: list[list[float]]) -> list[float]:
    """Aggregate multiple skill vectors into a single vector."""
    if not vectors:
        return [0.0, 0.0, 0.0, 0.0, 1.0]

    arr = np.array(vectors)
    return list(np.mean(arr, axis=0).round(3))
