from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional

from middleware.auth import get_current_user
from db.collections import Collections
from routes.passport import ARCHETYPES

router = APIRouter()


@router.get("/candidates")
async def get_candidates(
    archetype: Optional[str] = Query(None, description="Filter by archetype"),
    current_user: dict = Depends(get_current_user),
):
    """Get list of candidates with their passport data. Recruiters only."""
    if current_user["role"] != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can view candidates",
        )

    # Build query for candidate users
    user_query = {"role": "candidate"}
    users = await Collections.users().find(user_query).to_list(length=1000)

    candidates = []
    for user in users:
        user_id = user["_id"]

        # Get passport data
        passport = await Collections.passports().find_one({"user_id": user_id})

        # Apply archetype filter if specified
        user_archetype = passport.get("archetype") if passport else None
        if archetype and user_archetype != archetype:
            continue

        # Get session count
        sessions_completed = await Collections.sessions().count_documents(
            {"user_id": user_id, "submitted": True}
        )

        # Check if user has video
        has_video = False
        if passport and passport.get("interview_video_id"):
            video = await Collections.videos().find_one(
                {"_id": passport["interview_video_id"], "status": "ready"}
            )
            has_video = video is not None

        # Build archetype info
        archetype_label = None
        if user_archetype:
            archetype_info = ARCHETYPES.get(user_archetype, {})
            archetype_label = archetype_info.get("label", user_archetype)

        # Build metrics
        metrics = {}
        if passport and passport.get("metrics"):
            metrics = passport["metrics"]

        candidates.append({
            "user_id": user_id,
            "display_name": user.get("display_name", ""),
            "email": user.get("email", ""),
            "archetype": user_archetype,
            "archetype_label": archetype_label,
            "metrics": metrics,
            "sessions_completed": sessions_completed,
            "has_video": has_video,
        })

    return {
        "candidates": candidates,
        "total": len(candidates),
    }
