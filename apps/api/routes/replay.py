"""
Replay Routes - Session Timeline and Q&A

Provides endpoints for:
- GET /replay/{session_id}/timeline - Get unified session timeline
- POST /replay/{session_id}/ask - Natural language Q&A about the session
- GET /replay/{session_id}/insights - Get pre-computed quick insights
"""

from fastapi import APIRouter, HTTPException, Depends

from middleware.auth import get_current_user
from models.timeline import (
    Timeline,
    AskRequest,
    AskResponse,
    QuickInsightsResponse,
)
from services.replay import ReplayService
from db.collections import Collections


router = APIRouter()


@router.get("/{session_id}/timeline", response_model=Timeline)
async def get_session_timeline(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get the unified timeline for a coding session.

    Returns all events, code snapshots, diffs, interventions, and video timestamps
    combined into a single timeline for replay.

    Requires: The user must be the session owner or a recruiter.
    """
    # Verify session exists
    session = await Collections.sessions().find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check access permissions
    user_id = current_user.get("user_id")
    user_role = current_user.get("role", "candidate")
    session_owner = session.get("user_id")

    # Allow access if user owns the session or is a recruiter
    if user_id != session_owner and user_role != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied")

    # Build timeline
    service = ReplayService(session_owner)
    timeline = await service.build_timeline(session_id)

    if not timeline:
        raise HTTPException(status_code=404, detail="Failed to build timeline")

    return timeline


@router.post("/{session_id}/ask", response_model=AskResponse)
async def ask_about_session(
    session_id: str,
    request: AskRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Ask natural language questions about a coding session.

    Uses AI to analyze the session timeline and return answers with
    clickable references to specific moments in the timeline and video.

    Example questions:
    - "When did they change their approach?"
    - "Did they write tests before or after implementing?"
    - "How did they handle the off-by-one error?"
    - "What was their debugging strategy?"

    Requires: The user must be the session owner or a recruiter.
    """
    # Verify session exists
    session = await Collections.sessions().find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check access permissions
    user_id = current_user.get("user_id")
    user_role = current_user.get("role", "candidate")
    session_owner = session.get("user_id")

    if user_id != session_owner and user_role != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied")

    # Process question
    service = ReplayService(session_owner)
    response = await service.ask_about_session(
        session_id=session_id,
        question=request.question,
        include_video_search=request.include_video_search,
    )

    return response


@router.get("/{session_id}/insights", response_model=QuickInsightsResponse)
async def get_quick_insights(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get pre-computed quick insights about a coding session.

    Returns automatically detected patterns like:
    - Approach changes after errors
    - Debugging efficiency metrics
    - Testing habits
    - Notable struggle points

    Plus an AI-generated summary of the session.

    Requires: The user must be the session owner or a recruiter.
    """
    # Verify session exists
    session = await Collections.sessions().find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check access permissions
    user_id = current_user.get("user_id")
    user_role = current_user.get("role", "candidate")
    session_owner = session.get("user_id")

    if user_id != session_owner and user_role != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied")

    # Generate insights
    service = ReplayService(session_owner)
    insights = await service.generate_quick_insights(session_id)

    return insights


@router.get("/user/{user_id}/sessions")
async def get_user_sessions(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get all replayable sessions for a user.

    Returns a list of sessions with basic metadata for display
    on the candidate detail page.

    Requires: Recruiter role or own user_id.
    """
    # Check access permissions
    current_user_id = current_user.get("user_id")
    user_role = current_user.get("role", "candidate")

    if current_user_id != user_id and user_role != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch sessions with events (to ensure they're replayable)
    sessions_cursor = Collections.sessions().find(
        {"user_id": user_id}
    ).sort("started_at", -1)
    sessions = await sessions_cursor.to_list(length=50)

    result = []
    for session in sessions:
        session_id = session.get("session_id")

        # Get event count for this session
        event_count = await Collections.events().count_documents(
            {"session_id": session_id}
        )

        # Only include sessions with events
        if event_count == 0:
            continue

        # Get task info
        task_id = session.get("task_id")
        task = await Collections.tasks().find_one({"task_id": task_id})

        # Check if video is linked
        video = await Collections.videos().find_one({
            "session_id": session_id,
            "status": "ready"
        })

        # Get code history length
        code_history = session.get("code_history", [])

        result.append({
            "session_id": session_id,
            "task_id": task_id,
            "task_title": task.get("title", "Unknown") if task else "Unknown",
            "started_at": session.get("started_at"),
            "ended_at": session.get("ended_at"),
            "event_count": event_count,
            "code_snapshots": len(code_history),
            "has_video": video is not None,
            "video_id": str(video.get("_id")) if video else None,
        })

    return {"sessions": result}
