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


class VideoInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
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
