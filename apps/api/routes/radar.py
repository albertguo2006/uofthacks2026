"""
Radar Profile API Routes

Provides endpoints for:
- Fetching user's Engineering DNA radar profile
- Getting pending AI interventions (hints)
- Acknowledging hints
- Contextual hints based on code history (Feature 1)
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from bson import ObjectId

from middleware.auth import get_current_user
from db.collections import Collections
from services.ai_worker import acknowledge_intervention, track_intervention_effectiveness
from services.backboard import BackboardService
from services.amplitude import forward_to_amplitude
from services.user_error_profile import compute_error_profile, get_error_profile_summary

router = APIRouter()


class RadarDimension(BaseModel):
    score: float
    confidence: float


class RadarProfile(BaseModel):
    verification: Optional[RadarDimension] = None
    velocity: Optional[RadarDimension] = None
    optimization: Optional[RadarDimension] = None
    decomposition: Optional[RadarDimension] = None
    debugging: Optional[RadarDimension] = None


class Intervention(BaseModel):
    hint: Optional[str] = None
    hint_category: Optional[str] = None
    intervention_type: Optional[str] = None
    session_id: str
    triggered_at: Optional[datetime] = None


class RadarResponse(BaseModel):
    user_id: str
    radar_profile: Optional[dict] = None
    intervention: Optional[Intervention] = None
    radar_summary: Optional[str] = None


class AcknowledgeRequest(BaseModel):
    session_id: str


class EffectivenessRequest(BaseModel):
    session_id: str
    code_changed: bool
    issue_resolved: bool


@router.get("/{user_id}", response_model=RadarResponse)
async def get_radar_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get user's Engineering DNA radar profile with any pending interventions.
    """
    # Allow users to view their own profile, or recruiters to view any
    if current_user["user_id"] != user_id and current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code=403, detail="Not authorized to view this profile"
        )

    user = await Collections.users().find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get active session intervention status
    active_session = await Collections.sessions().find_one(
        {"user_id": user_id, "ended_at": None},
        sort=[("started_at", -1)],
    )

    intervention = None
    if active_session:
        ai_context = active_session.get("ai_context", {})
        if ai_context.get("is_stuck"):
            intervention = Intervention(
                hint=ai_context.get("last_hint"),
                hint_category=ai_context.get("hint_category"),
                intervention_type=ai_context.get("intervention_type"),
                session_id=active_session["session_id"],
                triggered_at=ai_context.get("stuck_since"),
            )

    return RadarResponse(
        user_id=user_id,
        radar_profile=user.get("radar_profile"),
        intervention=intervention,
        radar_summary=user.get("radar_summary"),
    )


@router.get("/me/profile", response_model=RadarResponse)
async def get_my_radar_profile(
    current_user: dict = Depends(get_current_user),
):
    """
    Get current user's Engineering DNA radar profile.
    """
    user_id = current_user["user_id"]
    user = await Collections.users().find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get active session intervention status
    active_session = await Collections.sessions().find_one(
        {"user_id": user_id, "ended_at": None},
        sort=[("started_at", -1)],
    )

    intervention = None
    if active_session:
        ai_context = active_session.get("ai_context", {})
        if ai_context.get("is_stuck"):
            intervention = Intervention(
                hint=ai_context.get("last_hint"),
                hint_category=ai_context.get("hint_category"),
                intervention_type=ai_context.get("intervention_type"),
                session_id=active_session["session_id"],
                triggered_at=ai_context.get("stuck_since"),
            )

    return RadarResponse(
        user_id=user_id,
        radar_profile=user.get("radar_profile"),
        intervention=intervention,
        radar_summary=user.get("radar_summary"),
    )


# =========================================================================
# ERROR PROFILE - User's historical error patterns (Adaptive Hints Feature)
# =========================================================================


class ErrorProfileResponse(BaseModel):
    dominant_category: str
    category_distribution: dict
    total_errors: int
    recent_trend: str
    effective_hint_styles: list
    has_data: bool
    summary: str


@router.get("/me/error-profile", response_model=ErrorProfileResponse)
async def get_my_error_profile(
    current_user: dict = Depends(get_current_user),
):
    """
    Get current user's error profile for transparency.
    Shows what error patterns have been detected and how hints are being personalized.
    """
    user_id = current_user["user_id"]

    # Compute error profile
    profile = await compute_error_profile(user_id)

    # Get human-readable summary
    summary = await get_error_profile_summary(user_id)

    return ErrorProfileResponse(
        dominant_category=profile.get("dominant_category", "logic"),
        category_distribution=profile.get("category_distribution", {}),
        total_errors=profile.get("total_errors", 0),
        recent_trend=profile.get("recent_trend", "stable"),
        effective_hint_styles=profile.get("effective_hint_styles", []),
        has_data=profile.get("has_data", False),
        summary=summary,
    )


@router.post("/intervention/acknowledge")
async def acknowledge_hint(
    request: AcknowledgeRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Acknowledge that the user has seen/dismissed a hint.
    Tracks hint_acknowledged event to Amplitude for analytics.
    """
    user_id = current_user["user_id"]

    # Get the intervention being acknowledged for analytics
    intervention = await Collections.interventions().find_one(
        {"session_id": request.session_id, "user_id": user_id, "acknowledged": False},
        sort=[("triggered_at", -1)],
    )

    # Acknowledge the intervention
    await acknowledge_intervention(request.session_id, user_id)

    # Track hint_acknowledged event to Amplitude
    event_id = str(ObjectId())
    event_doc = {
        "_id": event_id,
        "user_id": user_id,
        "session_id": request.session_id,
        "task_id": intervention.get("task_id") if intervention else None,
        "event_type": "hint_acknowledged",
        "timestamp": datetime.utcnow(),
        "properties": {
            "hint_category": intervention.get("hint_category") if intervention else None,
            "intervention_type": intervention.get("intervention_type") if intervention else None,
            "trigger_reason": intervention.get("trigger_reason") if intervention else None,
            "hint_style": intervention.get("hint_style") if intervention else None,
            "personalization_badge": intervention.get("personalization_badge") if intervention else None,
        },
        "forwarded_to_amplitude": False,
    }
    await Collections.events().insert_one(event_doc)

    # Forward to Amplitude in background
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=user_id,
        event_type="hint_acknowledged",
        timestamp=int(event_doc["timestamp"].timestamp() * 1000),
        properties={
            "session_id": request.session_id,
            "task_id": intervention.get("task_id") if intervention else None,
            "hint_category": intervention.get("hint_category") if intervention else None,
            "intervention_type": intervention.get("intervention_type") if intervention else None,
            "trigger_reason": intervention.get("trigger_reason") if intervention else None,
        },
    )

    return {"status": "acknowledged", "session_id": request.session_id}


@router.post("/intervention/effectiveness")
async def report_intervention_effectiveness(
    request: EffectivenessRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Report whether an intervention was effective.
    Called after user makes progress following a hint.
    Tracks hint_effectiveness event to Amplitude for analytics.
    """
    user_id = current_user["user_id"]

    # Get the most recent acknowledged intervention for this session
    intervention = await Collections.interventions().find_one(
        {"session_id": request.session_id, "user_id": user_id, "acknowledged": True},
        sort=[("triggered_at", -1)],
    )

    # Track effectiveness
    await track_intervention_effectiveness(
        session_id=request.session_id,
        user_id=user_id,
        code_changed=request.code_changed,
        issue_resolved=request.issue_resolved,
    )

    # Track hint_effectiveness event to Amplitude
    event_id = str(ObjectId())
    event_doc = {
        "_id": event_id,
        "user_id": user_id,
        "session_id": request.session_id,
        "task_id": intervention.get("task_id") if intervention else None,
        "event_type": "hint_effectiveness_reported",
        "timestamp": datetime.utcnow(),
        "properties": {
            "code_changed": request.code_changed,
            "issue_resolved": request.issue_resolved,
            "hint_category": intervention.get("hint_category") if intervention else None,
            "intervention_type": intervention.get("intervention_type") if intervention else None,
            "trigger_reason": intervention.get("trigger_reason") if intervention else None,
            "hint_style": intervention.get("hint_style") if intervention else None,
        },
        "forwarded_to_amplitude": False,
    }
    await Collections.events().insert_one(event_doc)

    # Forward to Amplitude in background
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=user_id,
        event_type="hint_effectiveness_reported",
        timestamp=int(event_doc["timestamp"].timestamp() * 1000),
        properties={
            "session_id": request.session_id,
            "code_changed": request.code_changed,
            "issue_resolved": request.issue_resolved,
            "hint_category": intervention.get("hint_category") if intervention else None,
            "trigger_reason": intervention.get("trigger_reason") if intervention else None,
        },
    )

    return {
        "status": "recorded",
        "session_id": request.session_id,
        "code_changed": request.code_changed,
        "issue_resolved": request.issue_resolved,
    }


@router.get("/session/{session_id}/intervention")
async def get_session_intervention(
    session_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Get the current intervention for a specific session.
    Tracks hint_displayed event when a hint is shown for the first time.
    """
    session = await Collections.sessions().find_one({"session_id": session_id})

    # Return empty intervention if session doesn't exist yet
    if not session:
        return {"intervention": None}

    if session.get("user_id") != current_user["user_id"]:
        raise HTTPException(
            status_code=403, detail="Not authorized to view this session"
        )

    ai_context = session.get("ai_context", {})

    if not ai_context.get("is_stuck"):
        return {"intervention": None}

    user_id = current_user["user_id"]

    # Track hint_displayed event (only once per intervention)
    # Check if we already tracked display for this hint
    hint_triggered_at = ai_context.get("stuck_since")
    if hint_triggered_at and not ai_context.get("display_tracked"):
        # Mark as tracked
        await Collections.sessions().update_one(
            {"session_id": session_id},
            {"$set": {"ai_context.display_tracked": True}}
        )

        # Track hint_displayed event to Amplitude
        event_id = str(ObjectId())
        event_doc = {
            "_id": event_id,
            "user_id": user_id,
            "session_id": session_id,
            "task_id": session.get("task_id"),
            "event_type": "hint_displayed",
            "timestamp": datetime.utcnow(),
            "properties": {
                "hint_category": ai_context.get("hint_category"),
                "intervention_type": ai_context.get("intervention_type"),
                "trigger_reason": ai_context.get("trigger_reason"),
                "hint_style": ai_context.get("hint_style"),
                "personalization_badge": ai_context.get("personalization_badge"),
            },
            "forwarded_to_amplitude": False,
        }
        await Collections.events().insert_one(event_doc)

        background_tasks.add_task(
            forward_to_amplitude,
            event_id=event_id,
            user_id=user_id,
            event_type="hint_displayed",
            timestamp=int(event_doc["timestamp"].timestamp() * 1000),
            properties={
                "session_id": session_id,
                "hint_category": ai_context.get("hint_category"),
                "intervention_type": ai_context.get("intervention_type"),
                "trigger_reason": ai_context.get("trigger_reason"),
            },
        )

    # Get the full intervention record for behavior analysis
    intervention_record = await Collections.interventions().find_one(
        {"session_id": session_id, "user_id": user_id},
        sort=[("triggered_at", -1)],
    )

    return {
        "intervention": {
            "hint": ai_context.get("last_hint"),
            "hint_category": ai_context.get("hint_category"),
            "intervention_type": ai_context.get("intervention_type"),
            "triggered_at": ai_context.get("stuck_since"),
            "analysis": ai_context.get("analysis"),
            "models_used": ai_context.get("models_used", []),
            "personalization_badge": ai_context.get("personalization_badge"),
            "hint_style": ai_context.get("hint_style"),
            "trigger_reason": ai_context.get("trigger_reason"),
            "behavior_analysis": intervention_record.get("behavior_analysis") if intervention_record else None,
        }
    }


# =========================================================================
# CONTEXTUAL HINTS - Enhanced with code history (Feature 1)
# =========================================================================


class ContextualHintRequest(BaseModel):
    session_id: str
    task_id: str
    current_code: str
    current_error: Optional[str] = None


class ContextualHintResponse(BaseModel):
    hint: str
    context: dict
    hint_id: str


# =========================================================================
# FRUSTRATION TRACKING - Real-time frustration level for hint unlocking
# =========================================================================

# Threshold for unlocking hints (0-1 scale)
FRUSTRATION_THRESHOLD = 0.5

# How much each "!" keypress boosts frustration (for demo)
DEMO_BOOST_AMOUNT = 0.15


class FrustrationBoostRequest(BaseModel):
    session_id: str
    task_id: str


class FrustrationStatusResponse(BaseModel):
    frustration_score: float
    threshold: float
    hint_unlocked: bool
    contributing_factors: dict
    demo_boosts: int


@router.get("/session/{session_id}/frustration", response_model=FrustrationStatusResponse)
async def get_frustration_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get current frustration level for a session.
    Used to determine if "Need a Hint?" button should be unlocked.
    """
    user_id = current_user["user_id"]

    # Get session
    session = await Collections.sessions().find_one({"session_id": session_id})

    if not session:
        # No session yet - return baseline
        return FrustrationStatusResponse(
            frustration_score=0.0,
            threshold=FRUSTRATION_THRESHOLD,
            hint_unlocked=False,
            contributing_factors={},
            demo_boosts=0,
        )

    # Get demo boost count from session
    demo_boosts = session.get("frustration_context", {}).get("demo_boosts", 0)
    demo_boost_score = min(0.5, demo_boosts * DEMO_BOOST_AMOUNT)  # Cap at 0.5 from boosts

    # Fetch recent events for natural frustration calculation
    recent_events = (
        await Collections.events()
        .find({"session_id": session_id})
        .sort("timestamp", -1)
        .limit(30)
        .to_list(30)
    )

    # Calculate natural frustration from behavior
    natural_frustration = calculate_natural_frustration(recent_events, session)

    # Combine natural + demo boost
    total_frustration = min(1.0, natural_frustration["score"] + demo_boost_score)

    return FrustrationStatusResponse(
        frustration_score=round(total_frustration, 2),
        threshold=FRUSTRATION_THRESHOLD,
        hint_unlocked=total_frustration >= FRUSTRATION_THRESHOLD,
        contributing_factors={
            **natural_frustration["factors"],
            "demo_boosts": demo_boosts,
            "demo_boost_score": round(demo_boost_score, 2),
        },
        demo_boosts=demo_boosts,
    )


@router.post("/session/{session_id}/frustration/boost")
async def boost_frustration(
    session_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Boost frustration level (triggered by '!' keypress during demo).
    Each boost adds DEMO_BOOST_AMOUNT to the frustration score.
    """
    user_id = current_user["user_id"]

    # Increment demo boost counter in session
    result = await Collections.sessions().find_one_and_update(
        {"session_id": session_id},
        {
            "$inc": {"frustration_context.demo_boosts": 1},
            "$set": {"frustration_context.last_boost": datetime.utcnow()},
        },
        upsert=True,
        return_document=True,
    )

    demo_boosts = result.get("frustration_context", {}).get("demo_boosts", 1) if result else 1
    demo_boost_score = min(0.5, demo_boosts * DEMO_BOOST_AMOUNT)

    # Track event to Amplitude
    event_id = str(ObjectId())
    event_doc = {
        "_id": event_id,
        "user_id": user_id,
        "session_id": session_id,
        "event_type": "frustration_boost",
        "timestamp": datetime.utcnow(),
        "properties": {
            "boost_number": demo_boosts,
            "demo_mode": True,
        },
        "forwarded_to_amplitude": False,
    }
    await Collections.events().insert_one(event_doc)

    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=user_id,
        event_type="frustration_boost",
        timestamp=int(event_doc["timestamp"].timestamp() * 1000),
        properties={
            "session_id": session_id,
            "boost_number": demo_boosts,
            "demo_mode": True,
        },
    )

    return {
        "status": "boosted",
        "demo_boosts": demo_boosts,
        "demo_boost_score": round(demo_boost_score, 2),
        "message": f"Frustration boosted! ({demo_boosts} boosts = +{round(demo_boost_score * 100)}%)",
    }


def calculate_natural_frustration(events: list, session: dict) -> dict:
    """
    Calculate natural frustration score from behavioral events.
    Returns score (0-1) and contributing factors.
    """
    factors = {
        "error_streak": 0,
        "time_stuck_minutes": 0,
        "failed_runs": 0,
        "minimal_progress": False,
    }

    if not events:
        return {"score": 0.0, "factors": factors}

    # Count error streak
    error_streak = 0
    for event in events:
        if event.get("event_type") == "error_emitted":
            error_streak += 1
        elif event.get("event_type") in ["test_cases_ran", "run_attempted"]:
            props = event.get("properties", {})
            if props.get("passed") or props.get("tests_passed", 0) > 0:
                break
    factors["error_streak"] = error_streak

    # Count failed runs
    failed_runs = sum(
        1 for e in events
        if e.get("event_type") in ["test_cases_ran", "run_attempted"]
        and not e.get("properties", {}).get("passed", False)
    )
    factors["failed_runs"] = failed_runs

    # Calculate time stuck (from session start or last success)
    session_start = session.get("started_at", datetime.utcnow())
    if isinstance(session_start, datetime):
        time_stuck_ms = (datetime.utcnow() - session_start).total_seconds() * 1000
        factors["time_stuck_minutes"] = round(time_stuck_ms / 60000, 1)

    # Check for minimal code changes
    code_events = [e for e in events if e.get("event_type") == "code_changed"]
    if len(code_events) < 3:
        factors["minimal_progress"] = True

    # Calculate score (0-1)
    score = 0.0

    # Error streak contribution (max 0.3)
    score += min(0.3, error_streak * 0.1)

    # Failed runs contribution (max 0.2)
    score += min(0.2, failed_runs * 0.04)

    # Time stuck contribution (max 0.3)
    score += min(0.3, factors["time_stuck_minutes"] * 0.05)

    # Minimal progress penalty (0.1)
    if factors["minimal_progress"]:
        score += 0.1

    return {"score": min(1.0, score), "factors": factors}


@router.post("/session/hints", response_model=ContextualHintResponse)
async def request_contextual_hint(
    request: ContextualHintRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Request a contextual hint based on the user's code history in the current session.
    Uses Backboard's Claude model for empathetic, pedagogical hints.
    """
    # Get session with code history
    session = await Collections.sessions().find_one({"session_id": request.session_id})
    
    if not session:
        # Create session if it doesn't exist
        session = {
            "session_id": request.session_id,
            "user_id": current_user["user_id"],
            "task_id": request.task_id,
            "code_history": [],
            "started_at": datetime.utcnow(),
        }
        await Collections.sessions().insert_one(session)
    
    if session.get("user_id") != current_user["user_id"]:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this session"
        )
    
    # Get task description
    task = await Collections.tasks().find_one({"task_id": request.task_id})
    task_description = task.get("description", "Unknown task") if task else "Unknown task"
    
    # Get code history from session
    code_history = session.get("code_history", [])
    
    # Generate contextual hint using Backboard
    backboard = BackboardService(current_user["user_id"])
    hint_result = await backboard.generate_contextual_hint(
        code_history=code_history,
        current_code=request.current_code,
        current_error=request.current_error,
        task_description=task_description,
        session_id=request.session_id,
    )
    
    # Store hint for tracking
    hint_id = str(ObjectId())
    await Collections.interventions().insert_one({
        "_id": hint_id,
        "session_id": request.session_id,
        "user_id": current_user["user_id"],
        "task_id": request.task_id,
        "triggered_at": datetime.utcnow(),
        "trigger_reason": "user_requested",
        "intervention_type": "contextual_hint",
        "hint_text": hint_result["hint"],
        "hint_context": hint_result["context"],
        "acknowledged": False,
    })

    # Update session ai_context so hint persists between polls
    await Collections.sessions().update_one(
        {"session_id": request.session_id},
        {
            "$set": {
                "ai_context.is_stuck": True,
                "ai_context.last_hint": hint_result["hint"],
                "ai_context.hint_category": "contextual",
                "ai_context.intervention_type": "user_requested",
                "ai_context.stuck_since": datetime.utcnow(),
            }
        },
    )
    
    # Track to Amplitude
    event_id = str(ObjectId())
    event_doc = {
        "_id": event_id,
        "user_id": current_user["user_id"],
        "session_id": request.session_id,
        "task_id": request.task_id,
        "event_type": "contextual_hint_shown",
        "timestamp": datetime.utcnow(),
        "properties": {
            "hint_category": "contextual",
            "code_history_length": len(code_history),
            "has_error": bool(request.current_error),
        },
        "forwarded_to_amplitude": False,
    }
    await Collections.events().insert_one(event_doc)
    
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=current_user["user_id"],
        event_type="contextual_hint_shown",
        timestamp=int(event_doc["timestamp"].timestamp() * 1000),
        properties={
            "session_id": request.session_id,
            "task_id": request.task_id,
            "hint_category": "contextual",
            "code_history_length": len(code_history),
        },
    )
    
    return ContextualHintResponse(
        hint=hint_result["hint"],
        context=hint_result["context"],
        hint_id=hint_id,
    )
