"""
Task Recommender Service

Personalized task recommendations based on:
1. Weak area practice (low radar scores)
2. Error pattern matching
3. Archetype matching
"""

from typing import Literal
from datetime import datetime, timedelta
from db.collections import Collections
from services.user_error_profile import compute_error_profile


ReasonType = Literal["weak_area", "archetype_match", "confidence_builder", "error_pattern"]


# Mapping of radar dimensions to task categories
DIMENSION_TO_CATEGORY = {
    "debugging": ["bugfix"],
    "verification": ["testing", "bugfix"],
    "optimization": ["optimization", "refactor"],
    "decomposition": ["feature", "refactor"],
    "velocity": ["feature"]
}

# Mapping of archetypes to preferred task categories
ARCHETYPE_PREFERENCES = {
    "fast_iterator": ["feature"],
    "debugger": ["bugfix"],
    "craftsman": ["refactor", "optimization"],
    "methodical": ["testing", "bugfix"],
    "explorer": ["feature"],
}

# Difficulty recommendations based on error patterns
ERROR_PATTERN_DIFFICULTY = {
    "syntax": "easy",  # Many syntax errors -> start easier
    "logic": "medium",
    "type": "easy",
    "runtime": "medium"
}


async def get_recommended_tasks(user_id: str, limit: int = 5) -> dict:
    """
    Get personalized task recommendations for a user.

    Returns:
    {
        "recommendations": [
            {
                "task": TaskSummary,
                "reason": "Recommended to strengthen your debugging skills",
                "reason_type": "weak_area" | "archetype_match" | "confidence_builder",
                "relevance_score": 0.85
            }
        ],
        "personalization_summary": "Based on 12 sessions and 45 error patterns"
    }
    """
    # Fetch user data
    user = await Collections.users().find_one({"_id": user_id})
    passport = await Collections.passports().find_one({"user_id": user_id})

    # Fetch error profile
    error_profile = await compute_error_profile(user_id)

    # Fetch completed tasks
    completed_tasks = await Collections.saved_code().find({
        "user_id": user_id,
        "passed": True
    }).to_list(100)
    completed_task_ids = {t["task_id"] for t in completed_tasks}

    # Count sessions
    session_count = await Collections.sessions().count_documents({"user_id": user_id})

    # Fetch all available tasks
    all_tasks = await Collections.tasks().find({}).to_list(100)

    # Filter out completed tasks
    available_tasks = [t for t in all_tasks if t["task_id"] not in completed_task_ids]

    if not available_tasks:
        return {
            "recommendations": [],
            "personalization_summary": "You've completed all available tasks!"
        }

    # Get radar profile and archetype
    radar_profile = user.get("radar_profile", {}) if user else {}
    archetype = passport.get("archetype") if passport else None

    # Score each task
    scored_tasks = []
    for task in available_tasks:
        score_result = score_task(
            task=task,
            radar_profile=radar_profile,
            archetype=archetype,
            error_profile=error_profile
        )
        scored_tasks.append({
            "task": task,
            **score_result
        })

    # Sort by relevance score
    scored_tasks.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Take top N
    recommendations = []
    for scored in scored_tasks[:limit]:
        task = scored["task"]

        # Handle both legacy (language) and new (languages) format
        languages = task.get("languages", [])
        if not languages and "language" in task:
            languages = [task["language"]]

        recommendations.append({
            "task": {
                "task_id": task["task_id"],
                "title": task["title"],
                "description": task.get("description", "")[:200] + ("..." if len(task.get("description", "")) > 200 else ""),
                "difficulty": task["difficulty"],
                "category": task["category"],
                "languages": languages,
                "estimated_minutes": 10 if task["difficulty"] == "easy" else 20 if task["difficulty"] == "medium" else 30,
                "proctored": task.get("proctored", False),
                "tags": task.get("tags", []),
            },
            "reason": scored["reason"],
            "reason_type": scored["reason_type"],
            "relevance_score": scored["relevance_score"]
        })

    # Generate personalization summary
    summary_parts = []
    if session_count > 0:
        summary_parts.append(f"{session_count} session{'s' if session_count != 1 else ''}")
    if error_profile.get("total_errors", 0) > 0:
        summary_parts.append(f"{error_profile['total_errors']} error patterns")

    personalization_summary = f"Based on {' and '.join(summary_parts)}" if summary_parts else "Based on your profile"

    return {
        "recommendations": recommendations,
        "personalization_summary": personalization_summary
    }


def score_task(
    task: dict,
    radar_profile: dict,
    archetype: str | None,
    error_profile: dict
) -> dict:
    """
    Score a task based on user profile.

    Returns:
    {
        "relevance_score": 0.0-1.0,
        "reason": "Human readable reason",
        "reason_type": "weak_area" | "archetype_match" | "confidence_builder" | "error_pattern"
    }
    """
    scores: list[tuple[float, str, ReasonType]] = []
    task_category = task.get("category", "feature")
    task_difficulty = task.get("difficulty", "medium")

    # 1. Weak area scoring (highest priority)
    if radar_profile:
        for dimension, dim_data in radar_profile.items():
            score = dim_data.get("score", 0.5) if isinstance(dim_data, dict) else dim_data
            if score < 0.5:  # Weak area
                matching_categories = DIMENSION_TO_CATEGORY.get(dimension, [])
                if task_category in matching_categories:
                    # Lower score = higher recommendation priority
                    relevance = 0.9 - (score * 0.4)  # 0.7-0.9 range
                    reason = get_weak_area_reason(dimension)
                    scores.append((relevance, reason, "weak_area"))

    # 2. Archetype matching
    if archetype:
        preferred_categories = ARCHETYPE_PREFERENCES.get(archetype, [])
        if task_category in preferred_categories:
            scores.append((0.7, get_archetype_reason(archetype), "archetype_match"))

    # 3. Error pattern based difficulty matching
    if error_profile.get("has_data"):
        dominant_category = error_profile.get("dominant_category", "logic")
        suggested_difficulty = ERROR_PATTERN_DIFFICULTY.get(dominant_category, "medium")

        if task_difficulty == suggested_difficulty:
            if error_profile.get("recent_trend") == "struggling":
                scores.append((0.65, "Matched to your current skill level for building confidence", "confidence_builder"))
            else:
                scores.append((0.5, "Good match for your experience level", "confidence_builder"))

    # 4. Default scoring for tasks that don't match any criteria
    if not scores:
        # Prefer easier tasks if user is struggling
        if error_profile.get("recent_trend") == "struggling":
            if task_difficulty == "easy":
                scores.append((0.4, "A good task to build momentum", "confidence_builder"))
            else:
                scores.append((0.2, "Available task", "confidence_builder"))
        else:
            scores.append((0.3, "Available task", "confidence_builder"))

    # Return highest scoring reason
    best_score = max(scores, key=lambda x: x[0])
    return {
        "relevance_score": round(best_score[0], 2),
        "reason": best_score[1],
        "reason_type": best_score[2]
    }


def get_weak_area_reason(dimension: str) -> str:
    """Get human-readable reason for weak area recommendation."""
    reasons = {
        "debugging": "Recommended to strengthen your debugging skills",
        "verification": "Recommended to improve your testing mindset",
        "optimization": "Recommended to enhance your optimization skills",
        "decomposition": "Recommended to practice code modularity",
        "velocity": "Recommended to increase your development velocity"
    }
    return reasons.get(dimension, f"Recommended to improve your {dimension} skills")


def get_archetype_reason(archetype: str) -> str:
    """Get human-readable reason for archetype-based recommendation."""
    reasons = {
        "fast_iterator": "Matches your fast iteration style",
        "debugger": "Suits your debugging expertise",
        "craftsman": "Aligned with your craftsman approach",
        "methodical": "Fits your methodical problem-solving style",
        "explorer": "Great for your exploratory approach"
    }
    return reasons.get(archetype, f"Matches your {archetype} profile")
