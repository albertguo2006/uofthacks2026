"""
AI Worker Service

Background task processor for:
- Intelligent frustration detection from behavioral patterns
- Triggering AI interventions (hints) based on Amplitude analytics
- Updating radar profiles based on behavior
- Personalized hints based on user's code and past problems
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from db.collections import Collections
from services.backboard import BackboardService
from services.user_error_profile import compute_error_profile
from config import get_settings

# Configure logging
logger = logging.getLogger("ai_worker")
logger.setLevel(logging.DEBUG)

# ANSI colors for console
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


async def trigger_analysis(session_id: str, user_id: str):
    """
    Intelligently analyze recent events and user behavior to decide when to trigger hints.
    Uses Amplitude-style behavioral analysis for smarter intervention timing.
    """
    print(f"\n{CYAN}╔═══════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}║ [AI Worker] trigger_analysis called                           ║{RESET}")
    print(f"{CYAN}║ Session: {session_id[:20]}...                              ║{RESET}")
    print(f"{CYAN}║ User: {user_id[:20]}...                                 ║{RESET}")
    print(f"{CYAN}╚═══════════════════════════════════════════════════════════════╝{RESET}")
    
    settings = get_settings()

    if not settings.ai_hint_enabled:
        print(f"{YELLOW}[AI Worker] ⚠ AI hints are DISABLED in settings{RESET}")
        return

    # Fetch session context
    session = await Collections.sessions().find_one({"session_id": session_id})
    print(f"{CYAN}[AI Worker] Session found: {session is not None}{RESET}")

    # Check if user recently acknowledged a hint - avoid spamming
    if session:
        ai_context = session.get("ai_context", {})
        if ai_context.get("is_stuck"):
            # Already showing a hint, don't trigger another
            print(f"{YELLOW}[AI Worker] ⚠ User already has active hint, skipping{RESET}")
            return

        # Check cooldown - don't show hints too frequently
        last_hint_time = ai_context.get("stuck_since")
        if last_hint_time and isinstance(last_hint_time, datetime):
            cooldown_ms = settings.hint_cooldown_ms if hasattr(settings, 'hint_cooldown_ms') else 60000
            if (datetime.utcnow() - last_hint_time).total_seconds() * 1000 < cooldown_ms:
                print(f"{YELLOW}[AI Worker] ⚠ Hint cooldown active, skipping{RESET}")
                return

    # Fetch recent events for this session
    recent_events = (
        await Collections.events()
        .find({"session_id": session_id})
        .sort("timestamp", -1)
        .limit(30)  # Increased to get better behavioral analysis
        .to_list(30)
    )

    print(f"{CYAN}[AI Worker] Found {len(recent_events)} recent events{RESET}")

    if not recent_events:
        print(f"{YELLOW}[AI Worker] ⚠ No recent events found, skipping{RESET}")
        return

    # Analyze behavioral patterns from events
    behavior_analysis = await analyze_user_behavior(user_id, session_id, recent_events)
    print(f"{CYAN}[AI Worker] Behavior analysis: error_streak={behavior_analysis.get('error_streak', 0)}, time_stuck={behavior_analysis.get('time_stuck_ms', 0)}ms{RESET}")

    # Intelligent intervention decision based on behavior patterns
    should_intervene, intervention_reason = should_show_hint(behavior_analysis, settings)
    print(f"{CYAN}[AI Worker] Should intervene: {should_intervene}, reason: {intervention_reason}{RESET}")

    if not should_intervene:
        print(f"{YELLOW}[AI Worker] ⚠ No intervention needed{RESET}")
        return

    print(f"{GREEN}[AI Worker] ✓ TRIGGERING AI HINT GENERATION!{RESET}")
    print(f"{MAGENTA}[AI Worker] Reason: {intervention_reason}{RESET}")

    # Fetch user's error profile for personalized hints
    error_profile = await compute_error_profile(user_id)
    print(f"{CYAN}[AI Worker] Error profile loaded: {error_profile.get('has_data', False)}{RESET}")

    # Get task information for context
    task_id = session.get("task_id") if session else None
    task = await Collections.tasks().find_one({"task_id": task_id}) if task_id else None

    # Build rich context for hint generation
    session_context = {
        "code": session.get("current_code_snapshot", "") if session else "",
        "last_error": behavior_analysis.get("last_error"),
        "error_streak": behavior_analysis.get("error_streak", 0),
        "time_stuck_ms": behavior_analysis.get("time_stuck_ms", 0),
        "attempt_count": (
            session.get("ai_context", {}).get("intervention_count", 0) + 1
            if session
            else 1
        ),
        # Enhanced context for smarter hints
        "recent_errors": behavior_analysis.get("recent_errors", []),
        "error_pattern": behavior_analysis.get("error_pattern"),
        "repeated_same_error": behavior_analysis.get("repeated_same_error", False),
        "tests_run_count": behavior_analysis.get("tests_run_count", 0),
        "tests_passed_trend": behavior_analysis.get("tests_passed_trend"),
        "code_change_frequency": behavior_analysis.get("code_change_frequency"),
        "task_description": task.get("description", "") if task else "",
        "task_difficulty": task.get("difficulty", "medium") if task else "medium",
        "intervention_reason": intervention_reason,
    }

    # Initialize Backboard with user context (enables memory)
    print(f"{CYAN}[AI Worker] Initializing BackboardService for user {user_id[:12]}...{RESET}")
    backboard = BackboardService(user_id)

    # Adaptive intervention - Backboard chooses the right model(s)
    print(f"{MAGENTA}[AI Worker] Calling adaptive_intervention (Claude/GPT-4/Gemini)...{RESET}")
    intervention = await backboard.adaptive_intervention(session_context, error_profile)

    print(f"{GREEN}[AI Worker] ✓ Intervention received!{RESET}")
    print(f"{CYAN}[AI Worker] Type: {intervention.get('type')}{RESET}")
    print(f"{CYAN}[AI Worker] Models used: {intervention.get('model_used', [])}{RESET}")
    print(f"{CYAN}[AI Worker] Hint preview: {intervention.get('hint', 'N/A')[:100]}...{RESET}")

    if intervention["type"] != "none":
        hint_category = categorize_hint(intervention)

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
                    "ai_context.personalization_badge": intervention.get("personalization_badge"),
                    "ai_context.hint_style": intervention.get("hint_style"),
                    "ai_context.hint_category": hint_category,
                    "ai_context.trigger_reason": intervention_reason,
                },
                "$inc": {"ai_context.intervention_count": 1},
            },
            upsert=True,  # Create session if it doesn't exist
        )

        # Store intervention for effectiveness tracking
        await Collections.interventions().insert_one(
            {
                "session_id": session_id,
                "user_id": user_id,
                "task_id": task_id,
                "triggered_at": datetime.utcnow(),
                "trigger_reason": intervention_reason,
                "intervention_type": intervention["type"],
                "models_used": intervention.get("model_used", []),
                "hint_text": intervention.get("hint"),
                "hint_category": hint_category,
                "analysis": intervention.get("analysis"),
                "personalization_badge": intervention.get("personalization_badge"),
                "hint_style": intervention.get("hint_style"),
                "behavior_analysis": behavior_analysis,  # Store for analytics
                "acknowledged": False,
                "code_changed_after": False,
                "resolved_issue": False,
            }
        )

    # Update radar profile
    await update_radar_profile(user_id, recent_events)


async def analyze_user_behavior(user_id: str, session_id: str, recent_events: list) -> dict:
    """
    Analyze user's behavioral patterns from recent events (Amplitude-style analysis).
    Returns rich behavioral context for intelligent hint triggering.
    """
    # Initialize analysis result
    analysis = {
        "error_streak": 0,
        "time_stuck_ms": 0,
        "last_error": None,
        "recent_errors": [],
        "error_pattern": None,
        "repeated_same_error": False,
        "tests_run_count": 0,
        "tests_passed_count": 0,
        "tests_passed_trend": "stable",
        "code_change_frequency": "normal",
        "total_events": len(recent_events),
        "frustration_score": 0.0,
    }

    if not recent_events:
        return analysis

    # Categorize events
    error_events = []
    run_events = []
    code_change_events = []

    for event in recent_events:
        event_type = event.get("event_type", "")
        props = event.get("properties", {})

        if event_type == "error_emitted":
            error_msg = props.get("error_message", "")
            error_events.append({
                "message": error_msg,
                "type": props.get("error_type", ""),
                "timestamp": event.get("timestamp"),
                "is_repeat": props.get("is_repeat", False),
            })
        elif event_type in ["run_attempted", "test_cases_ran"]:
            run_events.append({
                "passed": props.get("passed", False),
                "tests_passed": props.get("tests_passed", 0),
                "tests_total": props.get("tests_total", 0),
                "timestamp": event.get("timestamp"),
            })
        elif event_type == "code_changed":
            code_change_events.append({
                "lines_changed": props.get("lines_changed", 0),
                "chars_added": props.get("chars_added", 0),
                "timestamp": event.get("timestamp"),
            })

    # Calculate error streak (consecutive errors without success)
    analysis["error_streak"] = count_error_streak(recent_events)

    # Get recent errors with their messages
    analysis["recent_errors"] = [e["message"][:200] for e in error_events[:5]]

    # Set last error
    if error_events:
        analysis["last_error"] = error_events[0]["message"]

    # Detect repeated same error pattern
    if len(error_events) >= 2:
        error_messages = [e["message"][:100].lower() for e in error_events[:5]]
        # Check if same error repeated
        if len(set(error_messages)) == 1 and len(error_messages) >= 2:
            analysis["repeated_same_error"] = True
            analysis["error_pattern"] = "same_error_repeated"
        # Check if similar error types
        elif len(error_events) >= 3:
            error_types = [e["type"] for e in error_events[:5] if e["type"]]
            if error_types and error_types.count(error_types[0]) >= 3:
                analysis["error_pattern"] = f"repeated_{error_types[0]}_errors"

    # Calculate time stuck
    analysis["time_stuck_ms"] = calculate_time_stuck(recent_events)

    # Test run analysis
    analysis["tests_run_count"] = len(run_events)
    analysis["tests_passed_count"] = sum(1 for r in run_events if r.get("passed"))

    # Calculate tests passed trend (improving, declining, or stable)
    if len(run_events) >= 3:
        recent_passes = sum(1 for r in run_events[:3] if r.get("tests_passed", 0) > 0)
        older_passes = sum(1 for r in run_events[3:6] if r.get("tests_passed", 0) > 0)
        if recent_passes > older_passes:
            analysis["tests_passed_trend"] = "improving"
        elif recent_passes < older_passes:
            analysis["tests_passed_trend"] = "declining"

    # Analyze code change frequency
    if code_change_events:
        total_changes = sum(e.get("chars_added", 0) for e in code_change_events)
        if total_changes < 20:
            analysis["code_change_frequency"] = "minimal"  # Not making changes = stuck
        elif total_changes > 500:
            analysis["code_change_frequency"] = "high"  # Active coding

    # Calculate frustration score (0-1) based on multiple factors
    frustration_score = 0.0

    # Factor 1: Error streak (max 0.3)
    frustration_score += min(0.3, analysis["error_streak"] * 0.1)

    # Factor 2: Repeated same error (add 0.2)
    if analysis["repeated_same_error"]:
        frustration_score += 0.2

    # Factor 3: Time stuck (max 0.3)
    time_stuck_minutes = analysis["time_stuck_ms"] / 60000
    frustration_score += min(0.3, time_stuck_minutes * 0.1)

    # Factor 4: Declining test performance (add 0.1)
    if analysis["tests_passed_trend"] == "declining":
        frustration_score += 0.1

    # Factor 5: Minimal code changes (add 0.1)
    if analysis["code_change_frequency"] == "minimal":
        frustration_score += 0.1

    analysis["frustration_score"] = min(1.0, frustration_score)

    # Fetch historical context for this user
    historical = await get_user_historical_context(user_id)
    analysis["historical_context"] = historical

    return analysis


async def get_user_historical_context(user_id: str) -> dict:
    """
    Get user's historical behavior patterns for personalization.
    """
    # Get recent interventions to see what worked
    recent_interventions = await Collections.interventions().find({
        "user_id": user_id,
        "triggered_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
    }).sort("triggered_at", -1).limit(10).to_list(10)

    # Calculate hint effectiveness
    total_hints = len(recent_interventions)
    acknowledged_hints = sum(1 for i in recent_interventions if i.get("acknowledged"))
    effective_hints = sum(1 for i in recent_interventions if i.get("resolved_issue"))

    return {
        "hints_last_7_days": total_hints,
        "hint_acknowledgment_rate": acknowledged_hints / total_hints if total_hints > 0 else 0,
        "hint_effectiveness_rate": effective_hints / total_hints if total_hints > 0 else 0,
        "prefers_hints": total_hints > 0 and acknowledged_hints / total_hints > 0.5,
    }


def should_show_hint(behavior_analysis: dict, settings) -> tuple[bool, str]:
    """
    Intelligently decide whether to show a hint based on behavioral analysis.
    Returns (should_intervene, reason).
    """
    frustration_score = behavior_analysis.get("frustration_score", 0)
    error_streak = behavior_analysis.get("error_streak", 0)
    time_stuck_ms = behavior_analysis.get("time_stuck_ms", 0)
    repeated_same_error = behavior_analysis.get("repeated_same_error", False)
    tests_passed_trend = behavior_analysis.get("tests_passed_trend", "stable")
    code_change_frequency = behavior_analysis.get("code_change_frequency", "normal")
    
    print(f"\n{CYAN}[should_show_hint] Analyzing intervention triggers:{RESET}")
    print(f"  - frustration_score: {frustration_score:.2f} (threshold: 0.7 for high, 0.4 for moderate)")
    print(f"  - error_streak: {error_streak} (threshold: {getattr(settings, 'frustration_threshold_errors', 3)})")
    print(f"  - time_stuck_ms: {time_stuck_ms} (threshold: {getattr(settings, 'frustration_threshold_time_ms', 120000)})")
    print(f"  - repeated_same_error: {repeated_same_error}")
    print(f"  - tests_passed_trend: {tests_passed_trend}")
    print(f"  - code_change_frequency: {code_change_frequency}")

    # High frustration score = definitely show hint
    if frustration_score >= 0.7:
        print(f"{GREEN}[should_show_hint] ✓ TRIGGER: high_frustration_score{RESET}")
        return True, "high_frustration_score"

    # Multiple consecutive errors
    threshold_errors = getattr(settings, 'frustration_threshold_errors', 3)
    if error_streak >= threshold_errors:
        print(f"{GREEN}[should_show_hint] ✓ TRIGGER: error_streak ({error_streak} >= {threshold_errors}){RESET}")
        return True, "error_streak"

    # Same error repeated multiple times
    if repeated_same_error and error_streak >= 2:
        print(f"{GREEN}[should_show_hint] ✓ TRIGGER: repeated_same_error{RESET}")
        return True, "repeated_same_error"

    # Stuck for a long time without progress
    threshold_time = getattr(settings, 'frustration_threshold_time_ms', 120000)
    if time_stuck_ms >= threshold_time:
        print(f"{GREEN}[should_show_hint] ✓ TRIGGER: time_stuck ({time_stuck_ms} >= {threshold_time}){RESET}")
        return True, "time_stuck"

    # Moderate frustration with declining performance
    if frustration_score >= 0.4 and tests_passed_trend == "declining":
        print(f"{GREEN}[should_show_hint] ✓ TRIGGER: declining_performance{RESET}")
        return True, "declining_performance"

    # Moderate frustration with minimal code changes (really stuck)
    if frustration_score >= 0.4 and code_change_frequency == "minimal":
        print(f"{GREEN}[should_show_hint] ✓ TRIGGER: stuck_not_changing_code{RESET}")
        return True, "stuck_not_changing_code"

    # Historical context: if user generally finds hints helpful, lower threshold
    historical = behavior_analysis.get("historical_context", {})
    if historical.get("prefers_hints") and frustration_score >= 0.3:
        print(f"{GREEN}[should_show_hint] ✓ TRIGGER: user_prefers_hints{RESET}")
        return True, "user_prefers_hints"

    print(f"{YELLOW}[should_show_hint] ✗ No trigger conditions met{RESET}")
    return False, "no_intervention_needed"


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

    # Update intervention record (use find_one_and_update for sort support)
    await Collections.interventions().find_one_and_update(
        {"session_id": session_id, "user_id": user_id, "acknowledged": False},
        {"$set": {"acknowledged": True, "acknowledged_at": datetime.utcnow()}},
        sort=[("triggered_at", -1)],
    )


async def track_intervention_effectiveness(
    session_id: str, user_id: str, code_changed: bool, issue_resolved: bool
):
    """Track whether an intervention was effective."""
    # Use find_one_and_update for sort support
    await Collections.interventions().find_one_and_update(
        {"session_id": session_id, "user_id": user_id, "acknowledged": True},
        {
            "$set": {
                "code_changed_after": code_changed,
                "resolved_issue": issue_resolved,
                "resolution_tracked_at": datetime.utcnow(),
            }
        },
        sort=[("triggered_at", -1)],
    )
