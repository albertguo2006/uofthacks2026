from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional

from middleware.auth import get_current_user
from services.amplitude import fetch_event_segmentation, get_passport_analytics, fetch_user_event_counts

router = APIRouter()


class SessionStats(BaseModel):
    total_sessions: int
    passed_sessions: int
    pass_rate: float
    average_score: float


class ActivityMetrics(BaseModel):
    total_test_runs: int
    total_submissions: int
    runs_per_submission: float


class IntegrityMetrics(BaseModel):
    violations: int
    integrity_score: float


class PassportAnalyticsResponse(BaseModel):
    user_id: str
    event_summary: dict
    session_stats: SessionStats
    activity_metrics: ActivityMetrics
    integrity_metrics: IntegrityMetrics


@router.get("/passport", response_model=PassportAnalyticsResponse)
async def get_my_passport_analytics(
    current_user: dict = Depends(get_current_user),
):
    """
    Get comprehensive analytics for your skill passport.
    
    Returns:
    - Event counts (test runs, submissions, etc.)
    - Session statistics (pass rate, average score)
    - Activity metrics (runs per submission)
    - Integrity metrics (violations, integrity score)
    """
    try:
        analytics = await get_passport_analytics(current_user["user_id"])
        return PassportAnalyticsResponse(**analytics)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(exc)}",
        ) from exc


@router.get("/passport/{user_id}", response_model=PassportAnalyticsResponse)
async def get_user_passport_analytics(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get passport analytics for a specific user (recruiters only).
    """
    if current_user["role"] != "recruiter" and current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can view other users' analytics",
        )
    
    try:
        analytics = await get_passport_analytics(user_id)
        return PassportAnalyticsResponse(**analytics)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(exc)}",
        ) from exc


@router.get("/events/counts")
async def get_my_event_counts(
    current_user: dict = Depends(get_current_user),
):
    """Get event counts for the current user."""
    return await fetch_user_event_counts(current_user["user_id"])


@router.get("/amplitude/segmentation")
async def get_amplitude_segmentation(
    event_type: str = Query(..., min_length=1),
    start: str = Query(..., min_length=8, max_length=8),
    end: str = Query(..., min_length=8, max_length=8),
    interval: int = Query(1, ge=1),
    metric: str = Query("totals", min_length=1),
    current_user: dict = Depends(get_current_user),
):
    """Fetch Amplitude event segmentation data for the given event."""
    _ = current_user

    try:
        return await fetch_event_segmentation(
            event_type=event_type,
            start=start,
            end=end,
            interval=interval,
            metric=metric,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch data from Amplitude",
        ) from exc
