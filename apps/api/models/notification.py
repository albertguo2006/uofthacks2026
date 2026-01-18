from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class NotificationBase(BaseModel):
    recipient_id: str
    sender_id: Optional[str] = None
    type: Literal["interview_request", "application_status", "message", "system"]
    title: str
    message: str
    is_read: bool = False
    metadata: Optional[dict] = None  # For storing extra data like job_id, interview details, etc.


class NotificationCreate(NotificationBase):
    pass


class Notification(NotificationBase):
    notification_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None


class NotificationInDB(NotificationBase):
    id: str = Field(alias="_id")
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None


class InterviewRequest(BaseModel):
    candidate_id: str
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company_name: str
    interview_date: Optional[datetime] = None
    interview_type: Optional[Literal["phone", "video", "onsite", "technical"]] = None
    message: Optional[str] = None
    meeting_link: Optional[str] = None