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


@router.post("/intervention/acknowledge")
async def acknowledge_hint(
    request: AcknowledgeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Acknowledge that the user has seen/dismissed a hint.
    """
    await acknowledge_intervention(request.session_id, current_user["user_id"])

    return {"status": "acknowledged", "session_id": request.session_id}


@router.post("/intervention/effectiveness")
async def report_intervention_effectiveness(
    request: EffectivenessRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Report whether an intervention was effective.
    Called after user makes progress following a hint.
    """
    await track_intervention_effectiveness(
        session_id=request.session_id,
        user_id=current_user["user_id"],
        code_changed=request.code_changed,
        issue_resolved=request.issue_resolved,
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
    current_user: dict = Depends(get_current_user),
):
    """
    Get the current intervention for a specific session.
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

    return {
        "intervention": {
            "hint": ai_context.get("last_hint"),
            "hint_category": ai_context.get("hint_category"),
            "intervention_type": ai_context.get("intervention_type"),
            "triggered_at": ai_context.get("stuck_since"),
            "analysis": ai_context.get("analysis"),
            "models_used": ai_context.get("models_used", []),
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
