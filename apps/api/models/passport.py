from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Archetype(BaseModel):
    name: str
    label: str
    description: str
    confidence: float


class PassportMetrics(BaseModel):
    iteration_velocity: float = 0.0
    debug_efficiency: float = 0.0
    craftsmanship: float = 0.0
    tool_fluency: float = 0.0
    integrity: float = 1.0


class NotableMoment(BaseModel):
    type: str  # "achievement", "insight", etc.
    description: str
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class InterviewHighlight(BaseModel):
    timestamp: str  # "02:34"
    description: str
    query: str


class InterviewInfo(BaseModel):
    has_video: bool = False
    video_id: Optional[str] = None
    highlights: list[InterviewHighlight] = []


class SkillPassport(BaseModel):
    user_id: str
    display_name: str
    archetype: Optional[Archetype] = None
    skill_vector: list[float] = []
    metrics: PassportMetrics = Field(default_factory=PassportMetrics)
    sessions_completed: int = 0
    tasks_passed: int = 0
    notable_moments: list[NotableMoment] = []
    interview: InterviewInfo = Field(default_factory=InterviewInfo)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PassportInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    archetype: Optional[str] = None
    archetype_confidence: Optional[float] = None
    skill_vector: list[float] = []
    metrics: dict = Field(default_factory=dict)
    notable_sessions: list[dict] = []
    interview_video_id: Optional[str] = None
    interview_highlights: list[dict] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
