from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
import uuid

from middleware.auth import get_current_user
from db.collections import Collections
from models.proctoring import (
    ProctoringSession,
    ProctoringStatus,
    ProctoringViolation,
    StartProctoringRequest,
    StartProctoringResponse,
    ReportViolationRequest,
    ProctoringSessionResponse,
)

router = APIRouter()


@router.post("/start", response_model=StartProctoringResponse)
async def start_proctoring_session(
    request: StartProctoringRequest,
    current_user: dict = Depends(get_current_user),
):
    """Start a proctoring session after user agrees to terms."""
    # Verify task exists and is proctored
    task = await Collections.tasks().find_one({"task_id": request.task_id})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if not task.get("proctored", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not proctored",
        )

    # Check if there's already an active session for this user and task
    existing = await Collections.proctoring_sessions().find_one({
        "user_id": current_user["user_id"],
        "task_id": request.task_id,
        "status": ProctoringStatus.ACTIVE.value,
    })

    if existing:
        return StartProctoringResponse(
            session_id=existing["session_id"],
            task_id=existing["task_id"],
            status=ProctoringStatus(existing["status"]),
            camera_enabled=existing.get("camera_enabled", False),
        )

    # Create new proctoring session
    session_id = str(uuid.uuid4())
    session = ProctoringSession(
        session_id=session_id,
        user_id=current_user["user_id"],
        task_id=request.task_id,
        status=ProctoringStatus.ACTIVE,
        camera_enabled=request.camera_enabled,
        violations=[],
        started_at=datetime.utcnow(),
    )

    await Collections.proctoring_sessions().insert_one(session.model_dump())

    return StartProctoringResponse(
        session_id=session_id,
        task_id=request.task_id,
        status=ProctoringStatus.ACTIVE,
        camera_enabled=request.camera_enabled,
    )


@router.post("/{session_id}/violation")
async def report_violation(
    session_id: str,
    request: ReportViolationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Report a proctoring violation."""
    session = await Collections.proctoring_sessions().find_one({
        "session_id": session_id,
        "user_id": current_user["user_id"],
    })

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found",
        )

    if session["status"] != ProctoringStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proctoring session is not active",
        )

    violation = ProctoringViolation(
        violation_type=request.violation_type,
        timestamp=datetime.utcnow(),
        details=request.details,
    )

    await Collections.proctoring_sessions().update_one(
        {"session_id": session_id},
        {"$push": {"violations": violation.model_dump()}},
    )

    return {"success": True, "violation_type": request.violation_type}


@router.post("/{session_id}/end")
async def end_proctoring_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """End a proctoring session."""
    session = await Collections.proctoring_sessions().find_one({
        "session_id": session_id,
        "user_id": current_user["user_id"],
    })

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found",
        )

    await Collections.proctoring_sessions().update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": ProctoringStatus.ENDED.value,
                "ended_at": datetime.utcnow(),
            }
        },
    )

    return {"success": True, "status": ProctoringStatus.ENDED}


@router.get("/{session_id}", response_model=ProctoringSessionResponse)
async def get_proctoring_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get proctoring session status."""
    session = await Collections.proctoring_sessions().find_one({
        "session_id": session_id,
        "user_id": current_user["user_id"],
    })

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found",
        )

    return ProctoringSessionResponse(
        session_id=session["session_id"],
        user_id=session["user_id"],
        task_id=session["task_id"],
        status=ProctoringStatus(session["status"]),
        camera_enabled=session.get("camera_enabled", False),
        violation_count=len(session.get("violations", [])),
        started_at=session["started_at"],
        ended_at=session.get("ended_at"),
    )
