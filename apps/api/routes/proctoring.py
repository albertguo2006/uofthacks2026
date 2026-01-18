from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, UploadFile, File, Form
from datetime import datetime
import uuid
from bson import ObjectId
import aiofiles
import os

from middleware.auth import get_current_user
from db.collections import Collections
from services.amplitude import forward_to_amplitude
from services.twelvelabs import upload_video_to_twelvelabs
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
    background_tasks: BackgroundTasks,
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

    event_id = str(ObjectId())
    event_doc = {
        "_id": event_id,
        "user_id": current_user["user_id"],
        "session_id": session_id,
        "task_id": session["task_id"],
        "event_type": "proctoring_violation",
        "timestamp": datetime.utcnow(),
        "properties": {
            "violation_type": request.violation_type,
            "details": request.details,
        },
        "forwarded_to_amplitude": False,
        "processed_for_ml": False,
    }

    await Collections.events().insert_one(event_doc)
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=current_user["user_id"],
        event_type="proctoring_violation",
        timestamp=int(event_doc["timestamp"].timestamp() * 1000),
        properties={
            "session_id": session_id,
            "task_id": session["task_id"],
            "violation_type": request.violation_type,
            "details": request.details,
        },
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


@router.post("/upload-video", status_code=202)
async def upload_proctoring_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    session_id: str = Form(...),
    task_id: str = Form(...),
    is_proctored: str = Form("true"),
    current_user: dict = Depends(get_current_user),
):
    """Upload a proctored session video recording.

    This endpoint receives the video recording from the candidate's browser
    during a proctored coding session and processes it through TwelveLabs.
    """
    # Validate file type
    print(f"[DEBUG] Received video upload with content_type: {video.content_type}")
    print(f"[DEBUG] Filename: {video.filename}")

    # Allow various webm content types and octet-stream for browser compatibility
    allowed_types = [
        "video/mp4",
        "video/webm",
        "video/quicktime",
        "video/x-matroska",
        "application/octet-stream",  # Some browsers send this for webm
        "video/webm;codecs=vp9",      # WebM with VP9 codec
        "video/webm;codecs=vp8",      # WebM with VP8 codec
    ]

    # Check if content type starts with video/webm (to handle codec variations)
    if not (video.content_type in allowed_types or
            video.content_type.startswith("video/webm") or
            (video.content_type == "application/octet-stream" and video.filename.endswith(".webm"))):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {video.content_type} not allowed. Use mp4, webm, or mov.",
        )

    # Verify proctoring session exists and belongs to user
    session = await Collections.proctoring_sessions().find_one({
        "session_id": session_id,
        "user_id": current_user["user_id"],
    })

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found",
        )

    # Generate video ID
    video_id = str(ObjectId())

    # Create upload directory if needed
    UPLOAD_DIR = "/tmp/proctored_videos"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save file temporarily
    file_path = os.path.join(UPLOAD_DIR, f"{video_id}_{video.filename}")

    async with aiofiles.open(file_path, "wb") as f:
        content = await video.read()
        await f.write(content)

    # Create video document with correct content type
    video_doc = {
        "_id": video_id,
        "user_id": current_user["user_id"],
        "session_id": session_id,  # Proctoring session ID
        "task_id": task_id,
        "is_proctored": True,  # Mark as proctored video
        "status": "uploading",
        "filename": video.filename,
        "file_path": file_path,
        "content_type": "video/webm" if video.filename.endswith(".webm") else video.content_type,
        "uploaded_at": datetime.utcnow(),
        "uploaded_by": current_user["user_id"],  # Track who uploaded
    }

    await Collections.videos().insert_one(video_doc)

    # Update proctoring session with video ID
    await Collections.proctoring_sessions().update_one(
        {"session_id": session_id},
        {"$set": {"video_id": video_id}},
    )

    # Process video in background through TwelveLabs
    background_tasks.add_task(
        upload_video_to_twelvelabs,
        video_id=video_id,
        user_id=current_user["user_id"],
        file_path=file_path,
    )

    # Log event
    event_id = str(ObjectId())
    event_doc = {
        "_id": event_id,
        "user_id": current_user["user_id"],
        "session_id": session_id,
        "task_id": task_id,
        "event_type": "proctoring_video_uploaded",
        "timestamp": datetime.utcnow(),
        "properties": {
            "video_id": video_id,
            "file_size": len(content),
        },
        "forwarded_to_amplitude": False,
        "processed_for_ml": False,
    }

    await Collections.events().insert_one(event_doc)
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=current_user["user_id"],
        event_type="proctoring_video_uploaded",
        timestamp=int(event_doc["timestamp"].timestamp() * 1000),
        properties={
            "session_id": session_id,
            "task_id": task_id,
            "video_id": video_id,
        },
    )

    return {
        "video_id": video_id,
        "status": "uploading",
        "session_id": session_id,
        "message": "Video uploaded successfully and is being processed",
    }
