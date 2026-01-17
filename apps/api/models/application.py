from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Application(BaseModel):
    application_id: str
    job_id: str
    user_id: str
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, reviewed, accepted, rejected


class ApplicationCreate(BaseModel):
    job_id: str


class ApplicantInfo(BaseModel):
    application_id: str
    user_id: str
    display_name: str
    email: str
    applied_at: datetime
    fit_score: float
    archetype: Optional[str] = None
    archetype_label: Optional[str] = None
    sessions_completed: int = 0
    metrics: dict = {}
    status: str = "pending"
