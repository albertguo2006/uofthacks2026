from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class EventProperties(BaseModel):
    # Flexible properties for different event types
    command: Optional[str] = None
    source: Optional[str] = None  # "shortcut" | "menu"
    result: Optional[str] = None  # "pass" | "fail"
    error_type: Optional[str] = None
    lines_changed: Optional[int] = None
    chars_added: Optional[int] = None
    runtime_ms: Optional[int] = None
    tests_passed: Optional[int] = None
    tests_total: Optional[int] = None
    from_error_type: Optional[str] = None
    time_since_error_ms: Optional[int] = None
    chars_pasted: Optional[int] = None
    burst_ms: Optional[int] = None
    passed: Optional[bool] = None
    score: Optional[int] = None
    duration_ms: Optional[int] = None
    outcome: Optional[str] = None
    kind: Optional[str] = None
    loc_changed: Optional[int] = None
    count: Optional[int] = None
    scope: Optional[str] = None
    # Allow additional properties
    extra: Optional[dict[str, Any]] = None


class TrackEvent(BaseModel):
    event_type: str
    session_id: str
    task_id: str
    timestamp: int  # Unix ms
    properties: dict[str, Any] = Field(default_factory=dict)


class TrackEventResponse(BaseModel):
    event_id: str
    forwarded_to_amplitude: bool


class EventInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    session_id: str
    task_id: str
    event_type: str
    timestamp: datetime
    properties: dict[str, Any]
    forwarded_to_amplitude: bool = False
    processed_for_ml: bool = False

    class Config:
        populate_by_name = True
