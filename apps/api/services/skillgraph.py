import numpy as np
from datetime import datetime
from typing import Optional
from db.collections import Collections
from services.amplitude import update_amplitude_user_properties


def compute_job_fit(user_vector: list[float], job_vector: list[float]) -> float:
    """Compute cosine similarity between user and job vectors."""
    if not user_vector or not job_vector:
        return 0.0

    # Pad vectors to same length
    max_len = max(len(user_vector), len(job_vector))
    u = np.array(user_vector + [0.0] * (max_len - len(user_vector)))
    j = np.array(job_vector + [0.0] * (max_len - len(job_vector)))

    # Cosine similarity
    dot = np.dot(u, j)
    norm_u = np.linalg.norm(u)
    norm_j = np.linalg.norm(j)

    if norm_u == 0 or norm_j == 0:
        return 0.0

    return float(dot / (norm_u * norm_j))


async def extract_session_features(user_id: str, session_id: str) -> dict:
    """Extract features from a session's events."""
    cursor = Collections.events().find({
        "user_id": user_id,
        "session_id": session_id,
    }).sort("timestamp", 1)

    events = await cursor.to_list(length=1000)

    if not events:
        return {}

    # Feature extraction
    features = {
        "total_events": len(events),
        "run_attempts": 0,
        "errors_encountered": 0,
        "fixes_applied": 0,
        "commands_used": set(),
        "code_changes": 0,
        "paste_bursts": 0,
        "time_between_runs": [],
        "time_to_first_run": None,
        "shortcut_usage_ratio": 0,
    }

    first_event_time = events[0]["timestamp"] if events else None
    last_run_time = None
    total_commands = 0
    shortcut_commands = 0

    for event in events:
        event_type = event["event_type"]
        props = event.get("properties", {})

        if event_type == "run_attempted":
            features["run_attempts"] += 1
            if features["time_to_first_run"] is None and first_event_time:
                features["time_to_first_run"] = (
                    event["timestamp"] - first_event_time
                ).total_seconds()
            if last_run_time:
                features["time_between_runs"].append(
                    (event["timestamp"] - last_run_time).total_seconds()
                )
            last_run_time = event["timestamp"]

        elif event_type == "error_emitted":
            features["errors_encountered"] += 1

        elif event_type == "fix_applied":
            features["fixes_applied"] += 1

        elif event_type == "editor_command":
            features["commands_used"].add(props.get("command", ""))
            total_commands += 1
            if props.get("source") == "shortcut":
                shortcut_commands += 1

        elif event_type == "code_changed":
            features["code_changes"] += 1

        elif event_type == "paste_burst_detected":
            features["paste_bursts"] += 1

    # Compute derived metrics
    features["commands_used"] = list(features["commands_used"])
    if total_commands > 0:
        features["shortcut_usage_ratio"] = shortcut_commands / total_commands
    if features["time_between_runs"]:
        features["avg_time_between_runs"] = np.mean(features["time_between_runs"])

    return features


async def compute_skill_vector(user_id: str) -> list[float]:
    """Compute aggregate skill vector from all user sessions."""
    # Get all sessions
    cursor = Collections.sessions().find({
        "user_id": user_id,
        "submitted": True,
    })
    sessions = await cursor.to_list(length=100)

    if not sessions:
        return []

    # Aggregate features across sessions
    all_features = []
    for session in sessions:
        features = await extract_session_features(user_id, session["session_id"])
        if features:
            all_features.append(features)

    if not all_features:
        return []

    # Compute skill dimensions
    # [iteration_velocity, debug_efficiency, craftsmanship, tool_fluency, integrity]
    avg_runs = np.mean([f.get("run_attempts", 0) for f in all_features])
    avg_errors = np.mean([f.get("errors_encountered", 0) for f in all_features])
    avg_fixes = np.mean([f.get("fixes_applied", 0) for f in all_features])
    avg_shortcuts = np.mean([f.get("shortcut_usage_ratio", 0) for f in all_features])
    avg_paste_bursts = np.mean([f.get("paste_bursts", 0) for f in all_features])

    # Normalize to 0-1 range with reasonable bounds
    iteration_velocity = min(1.0, avg_runs / 20.0)  # More runs = faster iteration
    debug_efficiency = min(1.0, avg_fixes / max(avg_errors, 1))  # Fixes per error
    craftsmanship = max(0.0, 1.0 - (avg_errors / 10.0))  # Fewer errors = more craft
    tool_fluency = avg_shortcuts  # Already 0-1
    integrity = max(0.0, 1.0 - (avg_paste_bursts / 5.0))  # Penalize paste bursts

    return [
        round(iteration_velocity, 3),
        round(debug_efficiency, 3),
        round(craftsmanship, 3),
        round(tool_fluency, 3),
        round(integrity, 3),
    ]


async def assign_archetype(skill_vector: list[float]) -> tuple[str, float]:
    """Assign archetype based on skill vector using simple rules (or ML)."""
    if not skill_vector or len(skill_vector) < 5:
        return None, 0.0

    iteration_velocity = skill_vector[0]
    debug_efficiency = skill_vector[1]
    craftsmanship = skill_vector[2]
    tool_fluency = skill_vector[3]
    integrity = skill_vector[4]

    # Simple rule-based assignment (could be replaced with KMeans)
    archetypes_scores = {
        "fast_iterator": iteration_velocity * 0.5 + tool_fluency * 0.3 + debug_efficiency * 0.2,
        "careful_tester": craftsmanship * 0.4 + debug_efficiency * 0.4 + integrity * 0.2,
        "debugger": debug_efficiency * 0.5 + iteration_velocity * 0.3 + tool_fluency * 0.2,
        "craftsman": craftsmanship * 0.5 + integrity * 0.3 + debug_efficiency * 0.2,
        "explorer": iteration_velocity * 0.4 + debug_efficiency * 0.3 + craftsmanship * 0.3,
    }

    best_archetype = max(archetypes_scores, key=archetypes_scores.get)
    confidence = archetypes_scores[best_archetype]

    return best_archetype, round(confidence, 3)


async def update_passport_after_submit(
    user_id: str,
    session_id: str,
    task_id: str,
    passed: bool,
    score: int,
):
    """Update user's passport after task submission."""
    # Extract session features
    features = await extract_session_features(user_id, session_id)

    # Compute new skill vector
    skill_vector = await compute_skill_vector(user_id)

    # Assign archetype
    archetype, confidence = await assign_archetype(skill_vector)

    # Build metrics
    metrics = {
        "iteration_velocity": skill_vector[0] if len(skill_vector) > 0 else 0.0,
        "debug_efficiency": skill_vector[1] if len(skill_vector) > 1 else 0.0,
        "craftsmanship": skill_vector[2] if len(skill_vector) > 2 else 0.0,
        "tool_fluency": skill_vector[3] if len(skill_vector) > 3 else 0.0,
        "integrity": skill_vector[4] if len(skill_vector) > 4 else 1.0,
    }

    # Create notable moment if high score
    notable_session = None
    if passed and score >= 90:
        notable_session = {
            "session_id": session_id,
            "task_id": task_id,
            "highlight": f"Scored {score}% on {task_id}",
            "timestamp": datetime.utcnow(),
            "type": "achievement",
        }

    # Update passport
    update_doc = {
        "$set": {
            "skill_vector": skill_vector,
            "archetype": archetype,
            "archetype_confidence": confidence,
            "metrics": metrics,
            "updated_at": datetime.utcnow(),
        }
    }

    if notable_session:
        update_doc["$push"] = {"notable_sessions": notable_session}

    await Collections.passports().update_one(
        {"user_id": user_id},
        update_doc,
    )

    # Update user document too
    await Collections.users().update_one(
        {"_id": user_id},
        {
            "$set": {
                "skill_vector": skill_vector,
                "archetype": archetype,
                "integrity_score": metrics["integrity"],
            }
        },
    )

    # Update Amplitude user properties
    await update_amplitude_user_properties(
        user_id=user_id,
        properties={
            "skill_archetype": archetype,
            "skill_vector": skill_vector,
            "integrity_score": metrics["integrity"],
        },
    )


async def update_skill_proficiencies_after_submit(
    user_id: str,
    task_id: str,
    passed: bool,
    score: int,
):
    """Update user's skill proficiencies after task submission."""
    # Get task details to extract skills
    task = await Collections.tasks().find_one({"task_id": task_id})
    if not task:
        return

    # Get skills from task tags and category
    skills = []
    if task.get("tags"):
        skills.extend(task["tags"])
    if task.get("category"):
        skills.append(task["category"])

    if not skills:
        return

    # Get or create skill proficiencies document
    prof_doc = await Collections.skill_proficiencies().find_one({"user_id": user_id})
    proficiencies = prof_doc.get("proficiencies", {}) if prof_doc else {}

    # Update each skill's proficiency
    for skill in skills:
        skill_key = skill.lower().replace(" ", "_")

        if skill_key not in proficiencies:
            proficiencies[skill_key] = {
                "name": skill,
                "score": 0.0,
                "tasks_completed": 0,
                "total_score": 0,
                "last_updated": datetime.utcnow().isoformat(),
            }

        prof = proficiencies[skill_key]
        prof["tasks_completed"] += 1
        prof["total_score"] += score
        prof["score"] = prof["total_score"] / prof["tasks_completed"] / 100.0  # Normalize to 0-1
        prof["last_updated"] = datetime.utcnow().isoformat()

    # Upsert skill proficiencies document
    await Collections.skill_proficiencies().update_one(
        {"user_id": user_id},
        {
            "$set": {
                "proficiencies": proficiencies,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {
                "user_id": user_id,
            },
        },
        upsert=True,
    )
