"""
Chat models for Task Help Chat feature (Feature 3)
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatContext(BaseModel):
    code: Optional[str] = None
    error: Optional[str] = None
    test_results: Optional[dict] = None


class ChatMessage(BaseModel):
    session_id: str
    task_id: str
    message: str
    context: Optional[ChatContext] = None


class ChatResponse(BaseModel):
    response: str
    chat_id: str
    timestamp: datetime


class ChatHistoryEntry(BaseModel):
    chat_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    session_id: str
    task_id: str
    messages: list[ChatHistoryEntry]
