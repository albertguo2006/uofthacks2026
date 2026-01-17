"""
Timeline models for session replay feature.

These models represent the unified timeline of a coding session,
combining events, code snapshots, AI interventions, and video timestamps.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class TimelineEntry(BaseModel):
    """
    A single entry in the session timeline.
    Can represent code changes, runs, errors, AI interventions, etc.
    """
    id: str
    timestamp: datetime
    type: str  # "code_snapshot", "run_attempted", "error_emitted", "ai_intervention", "test_passed", "test_failed", etc.
    code_snapshot: Optional[str] = None
    code_diff: Optional[str] = None  # Unified diff from previous snapshot
    event_data: Optional[dict[str, Any]] = None
    video_timestamp_seconds: Optional[float] = None
    intervention: Optional[dict[str, Any]] = None
    label: str
    severity: Optional[str] = None  # "info", "warning", "error", "success"


class Timeline(BaseModel):
    """
    Full timeline response for a coding session.
    Aggregates all events, code history, interventions, and video info.
    """
    session_id: str
    user_id: str
    task_id: str
    task_title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int
    entries: list[TimelineEntry]
    has_video: bool
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    video_start_offset_seconds: float = 0  # Offset between session start and video start
    total_runs: int
    total_submissions: int
    errors_encountered: int
    interventions_received: int
    final_result: Optional[str] = None  # "passed", "failed", None


class TimelineJump(BaseModel):
    """Reference to a specific point in the timeline."""
    index: int
    timestamp: datetime
    description: str


class VideoSegment(BaseModel):
    """Reference to a segment in the video."""
    start_time: float
    end_time: float
    confidence: float
    description: Optional[str] = None


class AskRequest(BaseModel):
    """Request for natural language Q&A about the session."""
    question: str
    include_video_search: bool = True


class AskResponse(BaseModel):
    """
    Response to a natural language question about the session.
    Includes clickable references to timeline and video segments.
    """
    answer: str
    timeline_jumps: list[TimelineJump]
    video_segments: list[VideoSegment]
    confidence: float


class QuickInsight(BaseModel):
    """Pre-computed insight about the session."""
    category: str  # "approach_change", "debugging_efficiency", "testing_habit", "struggle_point"
    title: str
    description: str
    timeline_index: Optional[int] = None
    video_timestamp: Optional[float] = None


class QuickInsightsResponse(BaseModel):
    """Collection of auto-generated insights about the session."""
    session_id: str
    insights: list[QuickInsight]
    summary: str
