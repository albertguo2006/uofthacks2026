from fastapi import APIRouter, HTTPException, status, Depends

from middleware.auth import get_current_user
from db.collections import Collections
from models.passport import (
    SkillPassport,
    Archetype,
    PassportMetrics,
    NotableMoment,
    InterviewInfo,
    InterviewHighlight,
)

router = APIRouter()

# Archetype definitions
ARCHETYPES = {
    "fast_iterator": {
        "label": "Fast Iterator",
        "description": "Rapid prototyper who values quick feedback cycles and iterative improvement",
    },
    "careful_tester": {
        "label": "Careful Tester",
        "description": "Prioritizes test coverage and validation before shipping",
    },
    "debugger": {
        "label": "Systematic Debugger",
        "description": "Methodical problem-solver who excels at tracking down issues",
    },
    "craftsman": {
        "label": "Code Craftsman",
        "description": "Focuses on clean, maintainable code with attention to detail",
    },
    "explorer": {
        "label": "Explorer",
        "description": "Creative problem-solver who tries multiple approaches",
    },
}


@router.get("/{user_id}", response_model=SkillPassport)
async def get_passport(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get a user's skill passport."""
    # Allow viewing own passport or if recruiter
    if current_user["user_id"] != user_id and current_user["role"] != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this passport",
        )

    # Get user info
    user = await Collections.users().find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get passport
    passport = await Collections.passports().find_one({"user_id": user_id})
    if not passport:
        # Return empty passport
        return SkillPassport(
            user_id=user_id,
            display_name=user.get("display_name", ""),
        )

    # Get session stats
    sessions_completed = await Collections.sessions().count_documents(
        {"user_id": user_id, "submitted": True}
    )
    tasks_passed = await Collections.sessions().count_documents(
        {"user_id": user_id, "passed": True}
    )

    # Build archetype info
    archetype = None
    if passport.get("archetype"):
        archetype_info = ARCHETYPES.get(passport["archetype"], {})
        archetype = Archetype(
            name=passport["archetype"],
            label=archetype_info.get("label", passport["archetype"]),
            description=archetype_info.get("description", ""),
            confidence=passport.get("archetype_confidence", 0.0),
        )

    # Build metrics
    metrics_data = passport.get("metrics", {})
    metrics = PassportMetrics(
        iteration_velocity=metrics_data.get("iteration_velocity", 0.0),
        debug_efficiency=metrics_data.get("debug_efficiency", 0.0),
        craftsmanship=metrics_data.get("craftsmanship", 0.0),
        tool_fluency=metrics_data.get("tool_fluency", 0.0),
        integrity=metrics_data.get("integrity", 1.0),
    )

    # Build notable moments
    notable_moments = [
        NotableMoment(
            type=m.get("type", "achievement"),
            description=m.get("highlight", m.get("description", "")),
            session_id=m.get("session_id"),
            timestamp=m.get("timestamp"),
        )
        for m in passport.get("notable_sessions", [])
    ]

    # Build interview info
    interview = InterviewInfo(has_video=False)
    if passport.get("interview_video_id"):
        interview = InterviewInfo(
            has_video=True,
            highlights=[
                InterviewHighlight(
                    timestamp=f"{int(h['timestamp_start'] // 60):02d}:{int(h['timestamp_start'] % 60):02d}",
                    description=h.get("description", ""),
                    query=h.get("query_matched", ""),
                )
                for h in passport.get("interview_highlights", [])
            ],
        )

    return SkillPassport(
        user_id=user_id,
        display_name=user.get("display_name", ""),
        archetype=archetype,
        skill_vector=passport.get("skill_vector", []),
        metrics=metrics,
        sessions_completed=sessions_completed,
        tasks_passed=tasks_passed,
        notable_moments=notable_moments,
        interview=interview,
        updated_at=passport.get("updated_at"),
    )


@router.get("/me", response_model=SkillPassport)
async def get_my_passport(current_user: dict = Depends(get_current_user)):
    """Get the current user's skill passport."""
    return await get_passport(current_user["user_id"], current_user)
