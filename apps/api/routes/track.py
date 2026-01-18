from fastapi import APIRouter, Depends, BackgroundTasks
from datetime import datetime
from bson import ObjectId

from middleware.auth import get_current_user
from db.collections import Collections
from models.event import TrackEvent, TrackEventResponse
from services.amplitude import forward_to_amplitude
from services.ai_worker import trigger_analysis

router = APIRouter()

# ANSI colors for console
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


@router.post("", response_model=TrackEventResponse, status_code=202)
async def track_event(
    event: TrackEvent,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Ingest a behavioral event."""
    event_id = str(ObjectId())

    print(f"\n{CYAN}[Track] Event received: {event.event_type}{RESET}")
    print(f"{CYAN}[Track] Session: {event.session_id[:20] if event.session_id else 'N/A'}...{RESET}")

    # Convert timestamp from Unix ms to datetime
    event_timestamp = datetime.utcfromtimestamp(event.timestamp / 1000)

    # Store event
    event_doc = {
        "_id": event_id,
        "user_id": current_user["user_id"],
        "session_id": event.session_id,
        "task_id": event.task_id,
        "event_type": event.event_type,
        "timestamp": event_timestamp,
        "properties": event.properties,
        "forwarded_to_amplitude": False,
        "processed_for_ml": False,
    }

    await Collections.events().insert_one(event_doc)

    # Forward to Amplitude in background
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=current_user["user_id"],
        event_type=event.event_type,
        timestamp=event.timestamp,
        properties={
            **event.properties,
            "session_id": event.session_id,
            "task_id": event.task_id,
        },
    )

    # Trigger AI analysis for intervention detection on relevant events
    if event.event_type in ["run_attempted", "error_emitted", "code_changed"]:
        print(f"{MAGENTA}[Track] ⚡ Triggering AI analysis for event: {event.event_type}{RESET}")
        background_tasks.add_task(
            trigger_analysis,
            session_id=event.session_id,
            user_id=current_user["user_id"],
        )
    else:
        print(f"{YELLOW}[Track] Event {event.event_type} does not trigger AI analysis{RESET}")

    return TrackEventResponse(
        event_id=event_id,
        forwarded_to_amplitude=True,  # Will be forwarded async
    )


@router.post("/batch", status_code=202)
async def track_events_batch(
    events: list[TrackEvent],
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Ingest multiple behavioral events at once."""
    event_ids = []

    for event in events:
        event_id = str(ObjectId())
        event_ids.append(event_id)

        event_timestamp = datetime.utcfromtimestamp(event.timestamp / 1000)

        event_doc = {
            "_id": event_id,
            "user_id": current_user["user_id"],
            "session_id": event.session_id,
            "task_id": event.task_id,
            "event_type": event.event_type,
            "timestamp": event_timestamp,
            "properties": event.properties,
            "forwarded_to_amplitude": False,
            "processed_for_ml": False,
        }

        await Collections.events().insert_one(event_doc)

        background_tasks.add_task(
            forward_to_amplitude,
            event_id=event_id,
            user_id=current_user["user_id"],
            event_type=event.event_type,
            timestamp=event.timestamp,
            properties={
                **event.properties,
                "session_id": event.session_id,
                "task_id": event.task_id,
            },
        )

        # Trigger AI analysis for intervention detection on relevant events
        if event.event_type in ["run_attempted", "error_emitted", "code_changed"]:
            background_tasks.add_task(
                trigger_analysis,
                session_id=event.session_id,
                user_id=current_user["user_id"],
            )

    return {
        "event_ids": event_ids,
        "count": len(event_ids),
        "forwarded_to_amplitude": True,
    }
