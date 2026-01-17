"""
Recruiter API Routes (Feature 2 - Hiring Selection)

Provides AI-powered candidate ranking and analysis:
- GET /recruiter/candidates/ranked - Get AI-ranked candidates for a job
- GET /recruiter/candidates/{user_id}/analysis - Get detailed AI analysis for a candidate
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from bson import ObjectId

from middleware.auth import get_current_user
from db.collections import Collections
from services.backboard import BackboardService
from services.amplitude import forward_to_amplitude

router = APIRouter()


class CandidateRadar(BaseModel):
    verification: Optional[dict] = None
    velocity: Optional[dict] = None
    optimization: Optional[dict] = None
    decomposition: Optional[dict] = None
    debugging: Optional[dict] = None


class RankedCandidate(BaseModel):
    user_id: str
    display_name: str
    email: Optional[str] = None
    archetype: Optional[str] = None
    radar_profile: Optional[dict] = None
    sessions_completed: int
    integrity_score: Optional[float] = None
    ai_score: float
    ai_strengths: list[str]
    ai_gaps: list[str]
    ai_recommendation: str


class RankedCandidatesResponse(BaseModel):
    candidates: list[RankedCandidate]
    job_id: Optional[str] = None
    total_candidates: int
    ranking_timestamp: datetime


class CandidateAnalysis(BaseModel):
    user_id: str
    overall_score: float
    summary: str
    dimension_analysis: Optional[dict] = None
    key_strengths: list[str]
    areas_of_concern: list[str]
    interview_focus_areas: list[str]
    hiring_recommendation: str


def require_recruiter(current_user: dict = Depends(get_current_user)):
    """Dependency to ensure user is a recruiter."""
    if current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code=403,
            detail="Only recruiters can access this endpoint",
        )
    return current_user


@router.get("/candidates/ranked", response_model=RankedCandidatesResponse)
async def get_ranked_candidates(
    background_tasks: BackgroundTasks,
    job_id: Optional[str] = Query(None, description="Job ID to rank candidates for"),
    limit: int = Query(50, description="Maximum number of candidates to return"),
    current_user: dict = Depends(require_recruiter),
):
    """
    Get AI-ranked candidates for a job posting.
    Uses Backboard's GPT-4o model for intelligent ranking.
    """
    # Get job requirements if job_id provided
    job = None
    job_requirements = {}
    
    if job_id:
        job = await Collections.jobs().find_one({"job_id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        job_requirements = {
            "target_radar": job.get("target_radar", {}),
            "must_have": job.get("must_have", {}),
            "description": job.get("description", ""),
            "title": job.get("title", ""),
        }
    
    # Get all candidates
    candidates_cursor = Collections.users().find({
        "role": "candidate",
    }).limit(limit)
    
    candidates = []
    async for user in candidates_cursor:
        # Get session count
        sessions_count = await Collections.sessions().count_documents({
            "user_id": user["_id"],
            "submitted": True,
        })
        
        # Get passport for additional data
        passport = await Collections.passports().find_one({"user_id": user["_id"]})
        
        candidates.append({
            "user_id": user["_id"],
            "display_name": user.get("display_name", "Unknown"),
            "email": user.get("email"),
            "archetype": user.get("archetype") or (passport.get("archetype") if passport else None),
            "radar_profile": user.get("radar_profile", {}),
            "sessions_completed": sessions_count,
            "integrity_score": user.get("integrity_score"),
            "skill_vector": passport.get("skill_vector", []) if passport else [],
        })
    
    if not candidates:
        return RankedCandidatesResponse(
            candidates=[],
            job_id=job_id,
            total_candidates=0,
            ranking_timestamp=datetime.utcnow(),
        )
    
    # Get Amplitude data for candidates (if available)
    amplitude_data = {}
    # Note: In production, you'd fetch actual per-user analytics here
    # For now, we'll pass empty data and let the AI rank based on radar/sessions
    
    # Use Backboard to rank candidates
    backboard = BackboardService(current_user["user_id"])
    ranked_candidates = await backboard.rank_candidates(
        candidates=candidates,
        job_requirements=job_requirements,
        amplitude_data=amplitude_data,
    )
    
    # Convert to response model
    response_candidates = [
        RankedCandidate(
            user_id=c["user_id"],
            display_name=c["display_name"],
            email=c.get("email"),
            archetype=c.get("archetype"),
            radar_profile=c.get("radar_profile"),
            sessions_completed=c["sessions_completed"],
            integrity_score=c.get("integrity_score"),
            ai_score=c.get("ai_score", 0.5),
            ai_strengths=c.get("ai_strengths", []),
            ai_gaps=c.get("ai_gaps", []),
            ai_recommendation=c.get("ai_recommendation", ""),
        )
        for c in ranked_candidates
    ]
    
    # Track event to Amplitude
    event_id = str(ObjectId())
    event_doc = {
        "_id": event_id,
        "user_id": current_user["user_id"],
        "event_type": "candidate_ranking_viewed",
        "timestamp": datetime.utcnow(),
        "properties": {
            "job_id": job_id,
            "candidates_count": len(response_candidates),
        },
        "forwarded_to_amplitude": False,
    }
    await Collections.events().insert_one(event_doc)
    
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=current_user["user_id"],
        event_type="candidate_ranking_viewed",
        timestamp=int(event_doc["timestamp"].timestamp() * 1000),
        properties={
            "job_id": job_id,
            "candidates_count": len(response_candidates),
        },
    )
    
    return RankedCandidatesResponse(
        candidates=response_candidates,
        job_id=job_id,
        total_candidates=len(response_candidates),
        ranking_timestamp=datetime.utcnow(),
    )


@router.get("/candidates/{user_id}/analysis", response_model=CandidateAnalysis)
async def get_candidate_analysis(
    user_id: str,
    background_tasks: BackgroundTasks,
    job_id: Optional[str] = Query(None, description="Job ID to analyze fit for"),
    current_user: dict = Depends(require_recruiter),
):
    """
    Get detailed AI analysis for a specific candidate.
    """
    # Get candidate
    candidate = await Collections.users().find_one({"_id": user_id})
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Get passport
    passport = await Collections.passports().find_one({"user_id": user_id})
    
    # Get sessions count
    sessions_count = await Collections.sessions().count_documents({
        "user_id": user_id,
        "submitted": True,
    })
    
    # Prepare candidate data
    candidate_data = {
        "user_id": user_id,
        "display_name": candidate.get("display_name", "Unknown"),
        "archetype": candidate.get("archetype") or (passport.get("archetype") if passport else None),
        "radar_profile": candidate.get("radar_profile", {}),
        "sessions_completed": sessions_count,
        "integrity_score": candidate.get("integrity_score"),
        "skill_vector": passport.get("skill_vector", []) if passport else [],
    }
    
    # Get job if provided
    job = {}
    if job_id:
        job_doc = await Collections.jobs().find_one({"job_id": job_id})
        if job_doc:
            job = {
                "target_radar": job_doc.get("target_radar", {}),
                "title": job_doc.get("title", ""),
                "description": job_doc.get("description", ""),
            }
    
    # Get detailed analysis from Backboard
    backboard = BackboardService(current_user["user_id"])
    analysis = await backboard.explain_candidate_fit(
        candidate=candidate_data,
        job=job,
        amplitude_data=None,  # Could fetch actual analytics here
    )
    
    # Track event to Amplitude
    event_id = str(ObjectId())
    event_doc = {
        "_id": event_id,
        "user_id": current_user["user_id"],
        "event_type": "candidate_analysis_viewed",
        "timestamp": datetime.utcnow(),
        "properties": {
            "candidate_id": user_id,
            "job_id": job_id,
        },
        "forwarded_to_amplitude": False,
    }
    await Collections.events().insert_one(event_doc)
    
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=current_user["user_id"],
        event_type="candidate_analysis_viewed",
        timestamp=int(event_doc["timestamp"].timestamp() * 1000),
        properties={
            "candidate_id": user_id,
            "job_id": job_id,
        },
    )
    
    return CandidateAnalysis(
        user_id=user_id,
        overall_score=analysis.get("overall_score", 0.5),
        summary=analysis.get("summary", "Analysis unavailable"),
        dimension_analysis=analysis.get("dimension_analysis"),
        key_strengths=analysis.get("key_strengths", []),
        areas_of_concern=analysis.get("areas_of_concern", []),
        interview_focus_areas=analysis.get("interview_focus_areas", []),
        hiring_recommendation=analysis.get("hiring_recommendation", "maybe"),
    )


@router.get("/jobs")
async def list_jobs_for_recruiter(
    current_user: dict = Depends(require_recruiter),
):
    """
    List all jobs for the recruiter to select for candidate ranking.
    """
    jobs_cursor = Collections.jobs().find({})
    jobs = []
    
    async for job in jobs_cursor:
        jobs.append({
            "job_id": job["job_id"],
            "title": job["title"],
            "company": job.get("company", ""),
            "has_target_radar": bool(job.get("target_radar")),
        })
    
    return {"jobs": jobs}
