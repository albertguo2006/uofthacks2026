"""
AI Worker Service

Background task processor for:
- Frustration detection from event patterns
- Triggering AI interventions (hints)
- Updating radar profiles based on behavior
"""

from datetime import datetime, timedelta
from typing import Optional
from db.collections import Collections
from services.backboard import BackboardService
from config import get_settings


async def trigger_analysis(session_id: str, user_id: str):
    """
    Analyze recent events and potentially trigger an intervention.
    Called as a background task after relevant events.
    """
    settings = get_settings()

    if not settings.ai_hint_enabled:
        return

    # Initialize Backboard with user context (enables memory)
    backboard = BackboardService(user_id)

    # Fetch session context
    session = await Collections.sessions().find_one({"session_id": session_id})
    recent_events = (
        await Collections.events()
        .find({"session_id": session_id})
        .sort("timestamp", -1)
        .limit(15)
        .to_list(15)
    )

    if not recent_events:
        return

    # Build context for adaptive intervention
    error_events = [
        e for e in recent_events if e.get("event_type") == "error_emitted"
    ]

    session_context = {
        "code": session.get("current_code_snapshot", "") if session else "",
        "last_error": (
            error_events[0].get("properties", {}).get("error_message")
            if error_events
            else None
        ),
        "error_streak": count_error_streak(recent_events),
        "time_stuck_ms": calculate_time_stuck(recent_events),
        "attempt_count": (
            session.get("ai_context", {}).get("intervention_count", 0) + 1
            if session
            else 1
        ),
    }

    # Check if we should intervene based on thresholds
    should_intervene = (
        session_context["error_streak"] >= settings.frustration_threshold_errors
        or session_context["time_stuck_ms"] >= settings.frustration_threshold_time_ms
    )

    if not should_intervene:
        return

    # Adaptive intervention - Backboard chooses the right model(s)
    intervention = await backboard.adaptive_intervention(session_context)

    if intervention["type"] != "none":
        # Update session with intervention
        await Collections.sessions().update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "ai_context.is_stuck": True,
                    "ai_context.last_hint": intervention.get("hint"),
                    "ai_context.intervention_type": intervention["type"],
                    "ai_context.models_used": intervention.get("model_used", []),
                    "ai_context.analysis": intervention.get("analysis"),
                    "ai_context.stuck_since": datetime.utcnow(),
                },
                "$inc": {"ai_context.intervention_count": 1},
            },
        )

        # Store intervention for effectiveness tracking
        await Collections.interventions().insert_one(
            {
                "session_id": session_id,
                "user_id": user_id,
                "task_id": session.get("task_id") if session else None,
                "triggered_at": datetime.utcnow(),
                "trigger_reason": determine_trigger_reason(session_context),
                "intervention_type": intervention["type"],
                "models_used": intervention.get("model_used", []),
                "hint_text": intervention.get("hint"),
                "hint_category": categorize_hint(intervention),
                "analysis": intervention.get("analysis"),
                "acknowledged": False,
                "code_changed_after": False,
                "resolved_issue": False,
            }
        )

    # Update radar profile
    await update_radar_profile(user_id, recent_events)


def count_error_streak(events: list) -> int:
    """Count consecutive errors in recent events."""
    streak = 0
    for event in events:
        if event.get("event_type") == "error_emitted":
            streak += 1
        elif event.get("event_type") == "run_attempted":
            props = event.get("properties", {})
            if props.get("passed") or props.get("tests_passed", 0) > 0:
                break  # Success breaks the streak
    return streak


def calculate_time_stuck(events: list) -> int:
    """Calculate milliseconds since last successful action."""
    if not events:
        return 0

    now = datetime.utcnow()

    # Find last success (passed run or meaningful code change)
    for event in events:
        if event.get("event_type") == "run_attempted":
            props = event.get("properties", {})
            if props.get("passed"):
                event_time = event.get("timestamp")
                if isinstance(event_time, datetime):
                    return int((now - event_time).total_seconds() * 1000)
                return 0

    # No success found, calculate from oldest event in the window
    if events:
        oldest = events[-1].get("timestamp")
        if isinstance(oldest, datetime):
            return int((now - oldest).total_seconds() * 1000)

    return 0


def determine_trigger_reason(context: dict) -> str:
    """Determine why intervention was triggered."""
    if context.get("error_streak", 0) >= 3:
        return "error_streak"
    elif context.get("time_stuck_ms", 0) >= 180000:
        return "time_stuck"
    elif context.get("error_streak", 0) >= 2:
        return "repeated_pattern"
    return "unknown"


def categorize_hint(intervention: dict) -> str:
    """Categorize the hint type for analytics."""
    intervention_type = intervention.get("type", "")

    if intervention_type == "technical_hint":
        analysis = intervention.get("analysis", {})
        error_type = analysis.get("error_type", "")
        if error_type == "syntax":
            return "syntax"
        elif error_type in ["runtime", "type"]:
            return "logic"
        return "approach"
    elif intervention_type == "encouragement":
        return "encouragement"
    else:
        return "approach"


async def update_radar_profile(user_id: str, events: list):
    """
    Update user's Engineering DNA radar based on recent behavior.
    """
    if not events:
        return

    # Count semantic signals from recent events
    signals = {
        "test_events": 0,
        "refactor_events": 0,
        "error_fixes": 0,
        "function_definitions": 0,
        "run_attempts": 0,
        "successful_runs": 0,
        "imports_added": 0,
    }

    for event in events:
        event_type = event.get("event_type", "")
        props = event.get("properties", {})

        if "test" in event_type.lower():
            signals["test_events"] += 1
        if event_type == "refactor_initiated":
            signals["refactor_events"] += 1
        if event_type == "fix_applied":
            signals["error_fixes"] += 1
        if event_type == "semantic_block_added":
            signals["function_definitions"] += 1
        if event_type == "library_import":
            signals["imports_added"] += 1
        if event_type == "run_attempted":
            signals["run_attempts"] += 1
            if props.get("passed"):
                signals["successful_runs"] += 1

    # Calculate incremental score updates (small deltas)
    verification_delta = signals["test_events"] * 0.02
    optimization_delta = signals["refactor_events"] * 0.03
    debugging_delta = signals["error_fixes"] * 0.02
    decomposition_delta = signals["function_definitions"] * 0.02
    velocity_delta = (
        signals["run_attempts"] * 0.01
        if signals["run_attempts"] > 0
        else 0
    )

    # Only update if there are meaningful signals
    if any(
        [
            verification_delta,
            optimization_delta,
            debugging_delta,
            decomposition_delta,
            velocity_delta,
        ]
    ):
        # Get current user radar or initialize
        user = await Collections.users().find_one({"_id": user_id})
        current_radar = user.get("radar_profile", {}) if user else {}

        # Initialize radar if not exists
        if not current_radar:
            current_radar = {
                "verification": {"score": 0.5, "confidence": 0.3},
                "velocity": {"score": 0.5, "confidence": 0.3},
                "optimization": {"score": 0.5, "confidence": 0.3},
                "decomposition": {"score": 0.5, "confidence": 0.3},
                "debugging": {"score": 0.5, "confidence": 0.3},
            }

        # Apply updates with bounds [0, 1]
        def update_dimension(dim: str, delta: float):
            if dim in current_radar:
                new_score = min(1.0, max(0.0, current_radar[dim]["score"] + delta))
                new_confidence = min(
                    1.0, current_radar[dim]["confidence"] + 0.01
                )  # Confidence grows slowly
                current_radar[dim] = {
                    "score": round(new_score, 3),
                    "confidence": round(new_confidence, 3),
                }

        update_dimension("verification", verification_delta)
        update_dimension("velocity", velocity_delta)
        update_dimension("optimization", optimization_delta)
        update_dimension("decomposition", decomposition_delta)
        update_dimension("debugging", debugging_delta)

        # Update user document
        await Collections.users().update_one(
            {"_id": user_id}, {"$set": {"radar_profile": current_radar}}
        )


async def acknowledge_intervention(session_id: str, user_id: str):
    """Mark the current intervention as acknowledged."""
    # Update session
    await Collections.sessions().update_one(
        {"session_id": session_id},
        {"$set": {"ai_context.is_stuck": False}},
    )

    # Update intervention record
    await Collections.interventions().update_one(
        {"session_id": session_id, "user_id": user_id, "acknowledged": False},
        {"$set": {"acknowledged": True, "acknowledged_at": datetime.utcnow()}},
        sort=[("triggered_at", -1)],
    )


async def track_intervention_effectiveness(
    session_id: str, user_id: str, code_changed: bool, issue_resolved: bool
):
    """Track whether an intervention was effective."""
    await Collections.interventions().update_one(
        {"session_id": session_id, "user_id": user_id},
        {
            "$set": {
                "code_changed_after": code_changed,
                "resolved_issue": issue_resolved,
                "resolution_tracked_at": datetime.utcnow(),
            }
        },
        sort=[("triggered_at", -1)],
    )
