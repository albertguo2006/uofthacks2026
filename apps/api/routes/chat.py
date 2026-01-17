"""
Task Help Chat API Routes (Feature 3)

Provides Gemini-powered task help chat:
- Interactive Q&A about the current task
- Context-aware responses based on code and errors
- Full conversation history with Amplitude tracking
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime
from bson import ObjectId

from middleware.auth import get_current_user
from db.collections import Collections
from models.chat import ChatMessage, ChatResponse, ChatHistoryResponse, ChatHistoryEntry
from services.backboard import BackboardService
from services.amplitude import forward_to_amplitude

router = APIRouter()


@router.post("/task-help", response_model=ChatResponse)
async def task_help_chat(
    request: ChatMessage,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Send a message to the Gemini-powered task help assistant.
    Tracks all interactions to Amplitude.
    """
    # Get task details
    task = await Collections.tasks().find_one({"task_id": request.task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Validate session ownership
    session = await Collections.sessions().find_one({"session_id": request.session_id})
    if session and session.get("user_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized for this session")
    
    # Get current code from context or session
    current_code = ""
    current_error = None
    
    if request.context:
        current_code = request.context.code or ""
        current_error = request.context.error
    elif session:
        current_code = session.get("current_code_snapshot", "")
    
    # Generate response using Backboard/Gemini
    backboard = BackboardService(current_user["user_id"])
    response_text = await backboard.task_help_chat(
        task=task,
        current_code=current_code,
        question=request.message,
        session_id=request.session_id,
        error_context=current_error,
    )
    
    # Store chat message and response
    chat_id = str(ObjectId())
    timestamp = datetime.utcnow()
    
    # Store user message
    await Collections.chat_messages().insert_one({
        "_id": str(ObjectId()),
        "chat_id": chat_id,
        "session_id": request.session_id,
        "task_id": request.task_id,
        "user_id": current_user["user_id"],
        "role": "user",
        "content": request.message,
        "timestamp": timestamp,
        "context": request.context.model_dump() if request.context else None,
    })
    
    # Store assistant response
    await Collections.chat_messages().insert_one({
        "_id": str(ObjectId()),
        "chat_id": chat_id,
        "session_id": request.session_id,
        "task_id": request.task_id,
        "user_id": current_user["user_id"],
        "role": "assistant",
        "content": response_text,
        "timestamp": timestamp,
    })
    
    # Track request event to Amplitude
    request_event_id = str(ObjectId())
    request_event = {
        "_id": request_event_id,
        "user_id": current_user["user_id"],
        "session_id": request.session_id,
        "task_id": request.task_id,
        "event_type": "chat_help_requested",
        "timestamp": timestamp,
        "properties": {
            "message_length": len(request.message),
            "has_code_context": bool(current_code),
            "has_error_context": bool(current_error),
        },
        "forwarded_to_amplitude": False,
    }
    await Collections.events().insert_one(request_event)
    
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=request_event_id,
        user_id=current_user["user_id"],
        event_type="chat_help_requested",
        timestamp=int(timestamp.timestamp() * 1000),
        properties={
            "session_id": request.session_id,
            "task_id": request.task_id,
            "message_length": len(request.message),
        },
    )
    
    # Track response event to Amplitude
    response_event_id = str(ObjectId())
    response_event = {
        "_id": response_event_id,
        "user_id": current_user["user_id"],
        "session_id": request.session_id,
        "task_id": request.task_id,
        "event_type": "chat_help_response_received",
        "timestamp": timestamp,
        "properties": {
            "response_length": len(response_text),
        },
        "forwarded_to_amplitude": False,
    }
    await Collections.events().insert_one(response_event)
    
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=response_event_id,
        user_id=current_user["user_id"],
        event_type="chat_help_response_received",
        timestamp=int(timestamp.timestamp() * 1000),
        properties={
            "session_id": request.session_id,
            "task_id": request.task_id,
            "response_length": len(response_text),
        },
    )
    
    return ChatResponse(
        response=response_text,
        chat_id=chat_id,
        timestamp=timestamp,
    )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get chat history for a session.
    """
    # Get messages for this session
    messages_cursor = Collections.chat_messages().find({
        "session_id": session_id,
        "task_id": task_id,
        "user_id": current_user["user_id"],
    }).sort("timestamp", 1)
    
    messages = []
    async for msg in messages_cursor:
        messages.append(ChatHistoryEntry(
            chat_id=msg["chat_id"],
            role=msg["role"],
            content=msg["content"],
            timestamp=msg["timestamp"],
        ))
    
    return ChatHistoryResponse(
        session_id=session_id,
        task_id=task_id,
        messages=messages,
    )


@router.delete("/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Clear chat history for a session (also clears Backboard memory).
    """
    # Delete messages
    result = await Collections.chat_messages().delete_many({
        "session_id": session_id,
        "task_id": task_id,
        "user_id": current_user["user_id"],
    })
    
    # Clear Backboard memory for this session's chat
    backboard = BackboardService(current_user["user_id"])
    await backboard.clear_user_memory(f"session:{session_id}:chat")
    
    return {
        "status": "cleared",
        "session_id": session_id,
        "messages_deleted": result.deleted_count,
    }
