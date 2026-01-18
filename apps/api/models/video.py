from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VideoUpload(BaseModel):
    video_id: str
    status: str  # "uploading", "indexing", "ready", "failed"
    twelvelabs_task_id: Optional[str] = None


class VideoStatus(BaseModel):
    video_id: str
    status: str
    duration_seconds: Optional[int] = None
    ready_at: Optional[datetime] = None


class VideoHighlight(BaseModel):
    start_time: float
    end_time: float
    confidence: float
    transcript_snippet: str


class SearchResult(BaseModel):
    results: list[VideoHighlight]


class CommunicationScore(BaseModel):
    score: int
    reason: str


class CommunicationAnalysis(BaseModel):
    clarity: Optional[CommunicationScore] = None
    confidence: Optional[CommunicationScore] = None
    collaboration: Optional[CommunicationScore] = None
    technical_depth: Optional[CommunicationScore] = None


class InterviewHighlight(BaseModel):
    category: str
    query: str
    start: float
    end: float
    confidence: float
    transcript: Optional[str] = None


class VideoDetails(BaseModel):
    """Full video details including TwelveLabs analysis results."""
    video_id: str
    status: str
    duration_seconds: Optional[float] = None
    ready_at: Optional[datetime] = None
    summary: Optional[str] = None
    highlights: Optional[list[InterviewHighlight]] = None
    communication_analysis: Optional[CommunicationAnalysis] = None
    # Streaming URLs from TwelveLabs
    stream_url: Optional[str] = None  # HLS playlist URL
    thumbnail_url: Optional[str] = None  # Video thumbnail


class VideoInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    session_id: Optional[str] = None  # Link video to coding session for replay sync
    twelvelabs_index_id: Optional[str] = None
    twelvelabs_video_id: Optional[str] = None
    twelvelabs_task_id: Optional[str] = None
    status: str
    filename: str
    duration_seconds: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    ready_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
