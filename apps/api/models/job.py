from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class JobRequirements(BaseModel):
    min_integrity: Optional[float] = None
    min_sessions: Optional[int] = None
    required_archetypes: Optional[list[str]] = None


class UnlockRequirements(BaseModel):
    min_fit: float
    missing: list[str] = []


class Job(BaseModel):
    job_id: str
    title: str
    description: str
    company: str
    tier: int = Field(ge=0, le=2)
    target_vector: list[float]
    min_fit: float
    must_have: JobRequirements = Field(default_factory=JobRequirements)
    salary_range: str
    location: str
    tags: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobMatch(BaseModel):
    job_id: str
    title: str
    company: str
    tier: int
    fit_score: float
    unlocked: bool
    salary_range: str
    location: str
    tags: list[str] = []
    description: Optional[str] = None
    unlock_requirements: Optional[UnlockRequirements] = None


class JobsResponse(BaseModel):
    jobs: list[JobMatch]
    user_skill_vector: Optional[list[float]] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
