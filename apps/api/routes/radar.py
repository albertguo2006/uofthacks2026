"""
Radar Profile API Routes

Provides endpoints for:
- Fetching user's Engineering DNA radar profile
- Getting pending AI interventions (hints)
- Acknowledging hints
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from middleware.auth import get_current_user
from db.collections import Collections
from services.ai_worker import acknowledge_intervention, track_intervention_effectiveness

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

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

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
