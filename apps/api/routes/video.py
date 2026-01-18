from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query, BackgroundTasks
from datetime import datetime
from bson import ObjectId
import aiofiles
import os

from middleware.auth import get_current_user
from db.collections import Collections
from models.video import VideoUpload, VideoStatus, VideoDetails, SearchResult, VideoHighlight, InterviewHighlight, CommunicationAnalysis, CommunicationScore
from services.twelvelabs import upload_video_to_twelvelabs, search_video, get_video_streaming_info

router = APIRouter()

UPLOAD_DIR = "/tmp/video_uploads"


@router.post("/upload", response_model=VideoUpload, status_code=202)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: str = Query(None, description="Optional session ID to link video for replay sync"),
    current_user: dict = Depends(get_current_user),
):
    """Upload an interview video for processing.

    Optionally link to a coding session by providing session_id for
    timeline synchronization in the replay feature.
    """
    # Validate file type
    allowed_types = ["video/mp4", "video/webm", "video/quicktime"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Use mp4, webm, or mov.",
        )

    video_id = str(ObjectId())

    # Create upload directory if needed
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save file temporarily
    file_path = os.path.join(UPLOAD_DIR, f"{video_id}_{file.filename}")

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Create video document
    video_doc = {
        "_id": video_id,
        "user_id": current_user["user_id"],
        "session_id": session_id,  # Link to coding session for replay
        "status": "uploading",
        "filename": file.filename,
        "file_path": file_path,
        "uploaded_at": datetime.utcnow(),
    }

    await Collections.videos().insert_one(video_doc)

    # Process video in background
    background_tasks.add_task(
        upload_video_to_twelvelabs,
        video_id=video_id,
        user_id=current_user["user_id"],
        file_path=file_path,
    )

    return VideoUpload(
        video_id=video_id,
        status="uploading",
    )


@router.get("/{video_id}/status", response_model=VideoStatus)
async def get_video_status(
    video_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Check video processing status."""
    video = await Collections.videos().find_one({"_id": video_id})

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    # Check ownership - candidates can view own videos, recruiters can only view videos they uploaded
    is_owner = video["user_id"] == current_user["user_id"]
    is_uploader = video.get("uploaded_by") == current_user["user_id"]
    if not is_owner and not is_uploader:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this video",
        )

    return VideoStatus(
        video_id=video_id,
        status=video["status"],
        duration_seconds=video.get("duration_seconds"),
        ready_at=video.get("ready_at"),
    )


@router.get("/{video_id}/details", response_model=VideoDetails)
async def get_video_details(
    video_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get full video details including TwelveLabs analysis results.

    Returns summary, highlights, and communication analysis once video is ready.
    """
    video = await Collections.videos().find_one({"_id": video_id})

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    # Check ownership - candidates can view own videos, recruiters can only view videos they uploaded
    is_owner = video["user_id"] == current_user["user_id"]
    is_uploader = video.get("uploaded_by") == current_user["user_id"]
    if not is_owner and not is_uploader:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this video",
        )

    # Parse highlights if they exist
    highlights = None
    if video.get("highlights"):
        highlights = [
            InterviewHighlight(
                category=h.get("category", ""),
                query=h.get("query", ""),
                start=h.get("start", 0),
                end=h.get("end", 0),
                confidence=h.get("confidence", 0),
                transcript=h.get("transcript"),
            )
            for h in video["highlights"]
        ]

    # Parse communication analysis if it exists
    communication_analysis = None
    if video.get("communication_analysis"):
        ca = video["communication_analysis"]
        communication_analysis = CommunicationAnalysis(
            clarity=CommunicationScore(**ca["clarity"]) if ca.get("clarity") else None,
            confidence=CommunicationScore(**ca["confidence"]) if ca.get("confidence") else None,
            collaboration=CommunicationScore(**ca["collaboration"]) if ca.get("collaboration") else None,
            technical_depth=CommunicationScore(**ca["technical_depth"]) if ca.get("technical_depth") else None,
        )

    # Fetch streaming URLs from TwelveLabs if video is ready
    stream_url = None
    thumbnail_url = None
    duration_seconds = video.get("duration_seconds")

    if video["status"] == "ready" and video.get("twelvelabs_video_id"):
        streaming_info = await get_video_streaming_info(video["twelvelabs_video_id"])
        stream_url = streaming_info.get("stream_url")
        thumbnail_url = streaming_info.get("thumbnail_url")
        if streaming_info.get("duration"):
            duration_seconds = streaming_info["duration"]

    return VideoDetails(
        video_id=video_id,
        status=video["status"],
        duration_seconds=duration_seconds,
        ready_at=video.get("ready_at"),
        summary=video.get("summary"),
        highlights=highlights,
        communication_analysis=communication_analysis,
        stream_url=stream_url,
        thumbnail_url=thumbnail_url,
    )


@router.get("/{video_id}/search", response_model=SearchResult)
async def search_video_content(
    video_id: str,
    q: str = Query(..., description="Search query"),
    current_user: dict = Depends(get_current_user),
):
    """Search video for specific moments using TwelveLabs."""
    video = await Collections.videos().find_one({"_id": video_id})

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    # Check ownership - candidates can view own videos, recruiters can only view videos they uploaded
    is_owner = video["user_id"] == current_user["user_id"]
    is_uploader = video.get("uploaded_by") == current_user["user_id"]
    if not is_owner and not is_uploader:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to search this video",
        )

    if video["status"] != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video is not ready for searching",
        )

    # Search using TwelveLabs
    results = await search_video(
        twelvelabs_video_id=video.get("twelvelabs_video_id"),
        query=q,
    )

    return SearchResult(
        results=[
            VideoHighlight(
                start_time=r["start_time"],
                end_time=r["end_time"],
                confidence=r["confidence"],
                transcript_snippet=r.get("transcript", ""),
            )
            for r in results
        ]
    )


@router.delete("/{video_id}", status_code=204)
async def delete_video(
    video_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete an uploaded video."""
    video = await Collections.videos().find_one({"_id": video_id})

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    if video["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this video",
        )

    # Delete file if exists
    file_path = video.get("file_path")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    # Delete from database
    await Collections.videos().delete_one({"_id": video_id})

    # Update passport if this was the interview video
    await Collections.passports().update_one(
        {"user_id": current_user["user_id"], "interview_video_id": video_id},
        {"$set": {"interview_video_id": None, "interview_highlights": []}},
    )
