from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ViolationType(str, Enum):
    TAB_SWITCH = "tab_switch"
    WINDOW_BLUR = "window_blur"
    MOUSE_IDLE = "mouse_idle"
    RIGHT_CLICK = "right_click"
    COPY_PASTE = "copy_paste"
    BROWSER_DEVTOOLS = "browser_devtools"
    MULTIPLE_MONITORS = "multiple_monitors"


class ProctoringStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    TERMINATED = "terminated"


class ProctoringViolation(BaseModel):
    violation_type: ViolationType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[str] = None


class ProctoringAgreement(BaseModel):
    task_id: str
    camera_enabled: bool = False
    terms_accepted: bool = True
    accepted_at: datetime = Field(default_factory=datetime.utcnow)


class ProctoringSession(BaseModel):
    session_id: str
    user_id: str
    task_id: str
    status: ProctoringStatus = ProctoringStatus.ACTIVE
    camera_enabled: bool = False
    violations: list[ProctoringViolation] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None


class StartProctoringRequest(BaseModel):
    task_id: str
    camera_enabled: bool = False


class StartProctoringResponse(BaseModel):
    session_id: str
    task_id: str
    status: ProctoringStatus
    camera_enabled: bool


class ReportViolationRequest(BaseModel):
    violation_type: ViolationType
    details: Optional[str] = None


class ProctoringSessionResponse(BaseModel):
    session_id: str
    user_id: str
    task_id: str
    status: ProctoringStatus
    camera_enabled: bool
    violation_count: int
    started_at: datetime
    ended_at: Optional[datetime] = None
