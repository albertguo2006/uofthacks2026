"""
Proctoring Analysis API Routes
Phase 2: API endpoints for behavioral analysis of interview videos
"""

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId

from middleware.auth import get_current_user
from db.collections import Collections
from services.twelvelabs_behavior import (
    TwelveLabsBehaviorAnalyzer,
    analyze_video_background
)
from services.amplitude import forward_to_amplitude
from models.behavioral_analysis import (
    AnalyzeBehaviorRequest,
    AnalyzeBehaviorResponse,
    BehavioralAnalysisResult,
    BehaviorType,
    SeverityLevel
)

router = APIRouter(prefix="/proctoring", tags=["proctoring-analysis"])


@router.post("/{session_id}/analyze-video", response_model=AnalyzeBehaviorResponse)
async def analyze_proctoring_video(
    session_id: str,
    request: AnalyzeBehaviorRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger behavioral analysis for a proctoring video.
    This endpoint starts the analysis process in the background.

    Args:
        session_id: Proctoring session ID
        request: Analysis request with video_id
        background_tasks: FastAPI background tasks
        current_user: Authenticated user

    Returns:
        AnalyzeBehaviorResponse with status and analysis_id
    """
    # Verify session exists and belongs to user
    session = await Collections.proctoring_sessions().find_one({
        "session_id": session_id,
        "user_id": current_user["user_id"]
    })

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found"
        )

    # Verify video exists and is ready
    video = await Collections.videos().find_one({"_id": request.video_id})
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    if video.get("status") != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video is not ready for analysis. Current status: {video.get('status')}"
        )

    if not video.get("twelvelabs_video_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video has not been indexed by TwelveLabs"
        )

    # Check if analysis already exists (unless force reanalysis)
    if not request.force_reanalysis and video.get("behavioral_analysis"):
        return AnalyzeBehaviorResponse(
            video_id=request.video_id,
            session_id=session_id,
            analysis_status="completed",
            message="Analysis already exists. Use force_reanalysis=true to rerun.",
            analysis_id=request.video_id
        )

    # Create analysis record
    analysis_id = str(ObjectId())

    # Mark video as being analyzed
    await Collections.videos().update_one(
        {"_id": request.video_id},
        {"$set": {
            "behavioral_analysis_status": "in_progress",
            "behavioral_analysis_started_at": datetime.now(timezone.utc)
        }}
    )

    # Trigger background analysis
    background_tasks.add_task(
        analyze_video_background,
        video_id=request.video_id,
        session_id=session_id,
        user_id=current_user["user_id"],
        twelvelabs_video_id=video["twelvelabs_video_id"]
    )

    # Track event in Amplitude
    event_id = str(ObjectId())
    await Collections.events().insert_one({
        "_id": event_id,
        "user_id": current_user["user_id"],
        "session_id": session_id,
        "event_type": "behavioral_analysis_started",
        "timestamp": datetime.now(timezone.utc),
        "properties": {
            "video_id": request.video_id,
            "analysis_id": analysis_id,
            "force_reanalysis": request.force_reanalysis
        }
    })

    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=current_user["user_id"],
        event_type="behavioral_analysis_started",
        timestamp=int(datetime.now(timezone.utc).timestamp() * 1000),
        properties={
            "session_id": session_id,
            "video_id": request.video_id,
            "analysis_id": analysis_id
        }
    )

    return AnalyzeBehaviorResponse(
        video_id=request.video_id,
        session_id=session_id,
        analysis_status="started",
        message="Behavioral analysis has been started. Check status endpoint for results.",
        analysis_id=analysis_id
    )


@router.get("/{session_id}/behavioral-analysis", response_model=BehavioralAnalysisResult)
async def get_behavioral_analysis(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get behavioral analysis results for a proctoring session.

    Args:
        session_id: Proctoring session ID
        current_user: Authenticated user

    Returns:
        BehavioralAnalysisResult with analysis details
    """
    # Get session
    session = await Collections.proctoring_sessions().find_one({
        "session_id": session_id
    })

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found"
        )

    # Check access permissions (user or recruiter)
    if (session["user_id"] != current_user["user_id"] and
        current_user.get("role") != "recruiter"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session"
        )

    # Get associated video with analysis
    video = await Collections.videos().find_one({
        "session_id": session_id
    })

    if not video:
        return BehavioralAnalysisResult(
            session_id=session_id,
            analysis_status="pending",
            anomaly_summary="No video found for this session"
        )

    # Check if analysis exists
    if "behavioral_analysis" not in video or not video["behavioral_analysis"]:
        # Check if analysis is in progress
        if video.get("behavioral_analysis_status") == "in_progress":
            return BehavioralAnalysisResult(
                session_id=session_id,
                analysis_status="pending",
                anomaly_summary="Analysis in progress. Please check back later."
            )
        else:
            return BehavioralAnalysisResult(
                session_id=session_id,
                analysis_status="pending",
                anomaly_summary="Behavioral analysis not yet available. Please trigger analysis first."
            )

    # Get analysis data
    analysis = video["behavioral_analysis"]

    # Convert to response model
    from models.behavioral_analysis import SuspiciousSegment, BehavioralMetrics

    suspicious_segments = [
        SuspiciousSegment(**segment) for segment in analysis.get("suspicious_segments", [])
    ]

    behavioral_metrics = BehavioralMetrics(**analysis.get("behavioral_metrics", {}))

    return BehavioralAnalysisResult(
        session_id=session_id,
        analysis_status="complete",
        integrity_score=analysis.get("overall_integrity_score"),
        flagged_for_review=analysis.get("flagged_for_review"),
        suspicious_segments=suspicious_segments,
        behavioral_metrics=behavioral_metrics,
        anomaly_summary=analysis.get("anomaly_summary"),
        analyzed_at=analysis.get("analyzed_at")
    )


@router.get("/{session_id}/behavioral-highlights")
async def get_behavioral_highlights(
    session_id: str,
    behavior_type: Optional[BehaviorType] = None,
    severity: Optional[SeverityLevel] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get highlighted suspicious moments from a session's video.

    Args:
        session_id: Proctoring session ID
        behavior_type: Optional filter by behavior type
        severity: Optional filter by severity level
        limit: Maximum number of highlights to return
        current_user: Authenticated user

    Returns:
        List of behavioral highlights with timestamps
    """
    # Verify session access
    session = await Collections.proctoring_sessions().find_one({
        "session_id": session_id
    })

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proctoring session not found"
        )

    # Check permissions
    if (session["user_id"] != current_user["user_id"] and
        current_user.get("role") != "recruiter"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get video with analysis
    video = await Collections.videos().find_one({
        "session_id": session_id,
        "behavioral_analysis": {"$exists": True}
    })

    if not video or not video.get("behavioral_analysis"):
        return {"highlights": [], "message": "No analysis available"}

    # Extract segments
    analysis = video["behavioral_analysis"]
    segments = analysis.get("suspicious_segments", [])

    # Apply filters
    filtered_segments = segments
    if behavior_type:
        filtered_segments = [
            s for s in filtered_segments
            if s.get("behavior_type") == behavior_type.value
        ]
    if severity:
        filtered_segments = [
            s for s in filtered_segments
            if s.get("severity") == severity.value
        ]

    # Sort by confidence and limit
    filtered_segments.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    filtered_segments = filtered_segments[:limit]

    # Format as highlights
    from utils.behavioral_helpers import BehavioralAnalysisHelper
    helper = BehavioralAnalysisHelper()

    highlights = []
    for segment in filtered_segments:
        highlights.append({
            "segment_id": segment.get("segment_id"),
            "timestamp_start": helper.format_time(segment.get("start_time", 0)),
            "timestamp_end": helper.format_time(segment.get("end_time", 0)),
            "behavior": segment.get("behavior_type"),
            "severity": segment.get("severity"),
            "confidence": f"{segment.get('confidence', 0) * 100:.0f}%",
            "description": segment.get("description"),
            "thumbnail_url": segment.get("thumbnail_url")
        })

    return {
        "session_id": session_id,
        "highlights": highlights,
        "total_count": len(segments),
        "filtered_count": len(highlights)
    }


@router.get("/{session_id}/proctoring-report")
async def get_proctoring_report(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive proctoring report for a session.

    Args:
        session_id: Proctoring session ID
        current_user: Authenticated user

    Returns:
        Detailed proctoring report with all analysis data
    """
    # Check if user is recruiter
    if current_user.get("role") != "recruiter":
        # Regular users can only see their own reports
        session = await Collections.proctoring_sessions().find_one({
            "session_id": session_id,
            "user_id": current_user["user_id"]
        })
        if not session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this report"
            )
    else:
        # Recruiters can see any report
        session = await Collections.proctoring_sessions().find_one({
            "session_id": session_id
        })
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

    # Get proctoring report from database
    report = await Collections.db().proctoring_reports.find_one({
        "session_id": session_id
    })

    if not report:
        # Try to generate report if analysis exists
        video = await Collections.videos().find_one({
            "session_id": session_id,
            "behavioral_analysis": {"$exists": True}
        })

        if video and video.get("behavioral_analysis"):
            # Generate report on the fly
            from models.behavioral_analysis import BehavioralAnalysis
            analyzer = TwelveLabsBehaviorAnalyzer()

            analysis = BehavioralAnalysis(**video["behavioral_analysis"])
            report_data = await analyzer.generate_proctoring_report(
                video.get("twelvelabs_video_id", ""),
                analysis
            )

            # Store for future use
            await Collections.db().proctoring_reports.insert_one({
                "session_id": session_id,
                "user_id": session["user_id"],
                "report": report_data,
                "created_at": datetime.now(timezone.utc)
            })

            return report_data
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No proctoring report available for this session"
            )

    return report["report"]


@router.post("/compare-sessions")
async def compare_user_sessions(
    user_id: str,
    current_session_id: str,
    previous_session_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """
    Compare behavioral patterns across multiple sessions for a user.

    Args:
        user_id: User ID to analyze
        current_session_id: Current session to compare
        previous_session_ids: List of previous session IDs
        current_user: Authenticated user (must be recruiter)

    Returns:
        Comparison report showing behavioral patterns and trends
    """
    # Only recruiters can compare sessions
    if current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can compare sessions"
        )

    # Get current session analysis
    current_video = await Collections.videos().find_one({
        "session_id": current_session_id,
        "user_id": user_id,
        "behavioral_analysis": {"$exists": True}
    })

    if not current_video or not current_video.get("behavioral_analysis"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current session analysis not found"
        )

    # Get previous session analyses
    previous_analyses = []
    for session_id in previous_session_ids:
        video = await Collections.videos().find_one({
            "session_id": session_id,
            "user_id": user_id,
            "behavioral_analysis": {"$exists": True}
        })
        if video and video.get("behavioral_analysis"):
            from models.behavioral_analysis import BehavioralAnalysis
            analysis = BehavioralAnalysis(**video["behavioral_analysis"])
            previous_analyses.append(analysis)

    if not previous_analyses:
        return {
            "error": "No previous sessions with analysis found",
            "sessions_found": 0
        }

    # Perform comparison
    from models.behavioral_analysis import BehavioralAnalysis
    analyzer = TwelveLabsBehaviorAnalyzer()

    current_analysis = BehavioralAnalysis(**current_video["behavioral_analysis"])
    comparison = await analyzer.compare_sessions(
        user_id=user_id,
        current_analysis=current_analysis,
        previous_analyses=previous_analyses
    )

    return comparison


@router.get("/analysis-status/{video_id}")
async def get_analysis_status(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check the status of behavioral analysis for a video.

    Args:
        video_id: Video document ID
        current_user: Authenticated user

    Returns:
        Status information about the analysis
    """
    # Get video
    video = await Collections.videos().find_one({
        "_id": video_id
    })

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Check access
    if (video.get("user_id") != current_user["user_id"] and
        current_user.get("role") != "recruiter"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Determine status
    if video.get("behavioral_analysis"):
        analysis = video["behavioral_analysis"]
        return {
            "video_id": video_id,
            "status": "completed",
            "analyzed_at": analysis.get("analyzed_at"),
            "integrity_score": analysis.get("overall_integrity_score"),
            "flagged_for_review": analysis.get("flagged_for_review"),
            "summary": analysis.get("anomaly_summary")
        }
    elif video.get("behavioral_analysis_status") == "in_progress":
        return {
            "video_id": video_id,
            "status": "in_progress",
            "started_at": video.get("behavioral_analysis_started_at"),
            "message": "Analysis is currently running"
        }
    elif video.get("behavioral_analysis_error"):
        return {
            "video_id": video_id,
            "status": "failed",
            "error": video.get("behavioral_analysis_error"),
            "message": "Analysis failed. Please try again."
        }
    else:
        return {
            "video_id": video_id,
            "status": "not_started",
            "message": "Analysis has not been triggered yet"
        }


@router.delete("/{session_id}/behavioral-analysis")
async def delete_behavioral_analysis(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete behavioral analysis for a session (admin/testing only).

    Args:
        session_id: Session ID
        current_user: Authenticated user

    Returns:
        Deletion confirmation
    """
    # Only allow user to delete their own analysis
    session = await Collections.proctoring_sessions().find_one({
        "session_id": session_id,
        "user_id": current_user["user_id"]
    })

    if not session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete analysis for this session"
        )

    # Remove analysis from video
    result = await Collections.videos().update_one(
        {"session_id": session_id},
        {"$unset": {
            "behavioral_analysis": "",
            "behavioral_analysis_status": "",
            "behavioral_analysis_started_at": "",
            "behavioral_analysis_completed": "",
            "behavioral_analysis_error": ""
        }}
    )

    # Remove proctoring report
    await Collections.db().proctoring_reports.delete_one({
        "session_id": session_id
    })

    # Update proctoring session
    await Collections.proctoring_sessions().update_one(
        {"session_id": session_id},
        {"$unset": {
            "video_analyzed": "",
            "integrity_score": "",
            "flagged_for_review": "",
            "behavioral_analysis_id": ""
        }}
    )

    return {
        "success": True,
        "message": f"Behavioral analysis deleted for session {session_id}",
        "documents_modified": result.modified_count
    }