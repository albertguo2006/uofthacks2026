"""
Behavioral Analysis Models for TwelveLabs Integration
Phase 1: Data Schema Extensions for suspicious behavior detection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


# Enums for behavior types and severity levels

class BehaviorType(str, Enum):
    """Types of suspicious behaviors that can be detected"""
    # Visual behaviors
    LOOKING_AWAY = "looking_away"
    MULTIPLE_PEOPLE = "multiple_people"
    PHONE_USAGE = "phone_usage"
    READING_EXTERNAL = "reading_external"
    COVERING_CAMERA = "covering_camera"

    # Audio behaviors
    MULTIPLE_VOICES = "multiple_voices"
    WHISPERING = "whispering"
    BACKGROUND_VOICES = "background_voices"
    TYPING_WHILE_SPEAKING = "typing_while_speaking"

    # Environmental behaviors
    ENVIRONMENT_CHANGE = "environment_change"
    SCREEN_SHARING_ISSUES = "screen_sharing_issues"
    SUSPICIOUS_MOVEMENT = "suspicious_movement"


class SeverityLevel(str, Enum):
    """Severity levels for detected behaviors"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewStatus(str, Enum):
    """Review status for proctoring analysis"""
    CLEAN = "clean"
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    CLEARED = "cleared"


# Behavioral Analysis Models

class SuspiciousSegment(BaseModel):
    """A detected suspicious behavior segment in video"""
    segment_id: str
    start_time: float  # seconds
    end_time: float    # seconds
    behavior_type: BehaviorType
    confidence: float = Field(ge=0.0, le=1.0)  # 0-1 scale
    description: str
    severity: SeverityLevel
    thumbnail_url: Optional[str] = None


class BehavioralMetrics(BaseModel):
    """Aggregated behavioral metrics from video analysis"""
    eye_contact_consistency: float = Field(default=1.0, ge=0.0, le=1.0)
    environment_stability: float = Field(default=1.0, ge=0.0, le=1.0)
    audio_consistency: float = Field(default=1.0, ge=0.0, le=1.0)
    focus_score: float = Field(default=1.0, ge=0.0, le=1.0)


class DetectionStats(BaseModel):
    """Statistics about the detection process"""
    total_segments_analyzed: int = 0
    suspicious_segments_count: int = 0
    high_confidence_flags: int = 0


class BehavioralAnalysis(BaseModel):
    """Complete behavioral analysis results for a video"""
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_version: str = Field(default="1.0")

    # Detected suspicious segments
    suspicious_segments: List[SuspiciousSegment] = Field(default_factory=list)

    # Aggregated metrics
    behavioral_metrics: BehavioralMetrics = Field(default_factory=BehavioralMetrics)

    # Overall assessment
    overall_integrity_score: float = Field(default=1.0, ge=0.0, le=1.0)
    flagged_for_review: bool = False
    review_required_reasons: List[str] = Field(default_factory=list)
    anomaly_summary: str = "No suspicious behaviors detected during the interview."

    # Detection statistics
    detection_stats: DetectionStats = Field(default_factory=DetectionStats)


# Extended Video Model with Behavioral Analysis

class VideoWithBehavioralAnalysis(BaseModel):
    """Extended video model including behavioral analysis"""
    # Existing video fields
    id: str = Field(alias="_id")
    user_id: str
    session_id: Optional[str] = None
    twelvelabs_index_id: Optional[str] = None
    twelvelabs_video_id: Optional[str] = None
    twelvelabs_task_id: Optional[str] = None
    status: str
    filename: str
    duration_seconds: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    ready_at: Optional[datetime] = None

    # New: Behavioral analysis field
    behavioral_analysis: Optional[BehavioralAnalysis] = None

    class Config:
        populate_by_name = True


# Proctoring Metrics for Passport

class BehavioralPattern(BaseModel):
    """Common behavioral patterns for a candidate"""
    consistent_environment: bool = True
    maintains_focus: bool = True
    professional_conduct: bool = True


class CommonFlag(BaseModel):
    """Commonly flagged behaviors for a candidate"""
    behavior_type: BehaviorType
    frequency: int = 0
    last_occurrence: Optional[datetime] = None


class ProctoringMetrics(BaseModel):
    """Proctoring metrics to be added to candidate passport"""
    # Overall integrity across all sessions
    overall_integrity_score: float = Field(default=1.0, ge=0.0, le=1.0)
    total_sessions_analyzed: int = 0
    flagged_sessions_count: int = 0

    # Behavioral patterns
    behavioral_patterns: BehavioralPattern = Field(default_factory=BehavioralPattern)

    # Common flags across sessions
    common_flags: List[CommonFlag] = Field(default_factory=list)

    # Review status
    review_status: ReviewStatus = ReviewStatus.CLEAN
    reviewer_notes: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None


# Extended Passport Model with Proctoring Metrics

class PassportWithProctoring(BaseModel):
    """Extended passport model including proctoring metrics"""
    # Existing passport fields
    id: str = Field(alias="_id")
    user_id: str
    archetype: Optional[str] = None
    archetype_confidence: Optional[float] = None
    skill_vector: List[float] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)
    notable_sessions: List[dict] = Field(default_factory=list)
    interview_video_id: Optional[str] = None
    interview_highlights: List[dict] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # New: Proctoring metrics field
    proctoring_metrics: Optional[ProctoringMetrics] = None

    class Config:
        populate_by_name = True


# Request/Response Models for API

class AnalyzeBehaviorRequest(BaseModel):
    """Request to analyze a video for suspicious behaviors"""
    video_id: str
    session_id: str
    force_reanalysis: bool = False


class AnalyzeBehaviorResponse(BaseModel):
    """Response from behavioral analysis"""
    video_id: str
    session_id: str
    analysis_status: Literal["started", "in_progress", "completed", "failed"]
    message: str
    analysis_id: Optional[str] = None


class BehavioralAnalysisResult(BaseModel):
    """Result of behavioral analysis for API responses"""
    session_id: str
    analysis_status: Literal["pending", "complete", "failed"]
    integrity_score: Optional[float] = None
    flagged_for_review: Optional[bool] = None
    suspicious_segments: Optional[List[SuspiciousSegment]] = None
    behavioral_metrics: Optional[BehavioralMetrics] = None
    anomaly_summary: Optional[str] = None
    analyzed_at: Optional[datetime] = None


class ProctoringSessionUpdate(BaseModel):
    """Update model for proctoring session with behavioral analysis"""
    video_analyzed: bool = False
    integrity_score: Optional[float] = None
    flagged_for_review: Optional[bool] = None
    behavioral_analysis_id: Optional[str] = None


# Utility Models

class BehaviorQuery(BaseModel):
    """Query configuration for detecting specific behaviors"""
    behavior_type: BehaviorType
    search_query: str
    severity: SeverityLevel
    confidence_threshold: float = 0.5


class IntegrityThresholds(BaseModel):
    """Configurable thresholds for integrity scoring"""
    clean_threshold: float = 0.85  # Above this is clean
    review_threshold: float = 0.7  # Below this needs review
    flag_threshold: float = 0.5    # Below this is automatic flag

    # Behavior count thresholds
    max_high_severity_behaviors: int = 2
    max_total_suspicious_segments: int = 5


# Summary Statistics Model

class BehavioralAnalyticsSummary(BaseModel):
    """Summary statistics for a user's behavioral analytics"""
    user_id: str
    total_videos_analyzed: int = 0
    average_integrity_score: float = Field(default=1.0, ge=0.0, le=1.0)

    # Breakdown by behavior type
    behavior_frequency: dict[str, int] = Field(default_factory=dict)

    # Trends
    integrity_trend: Literal["improving", "stable", "declining"] = "stable"
    last_session_score: Optional[float] = None

    # Recommendations
    requires_manual_review: bool = False
    review_priority: Literal["low", "medium", "high"] = "low"