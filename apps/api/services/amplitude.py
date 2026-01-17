import httpx
import json
from config import get_settings
from db.collections import Collections

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


async def forward_to_amplitude(
    event_id: str,
    user_id: str,
    event_type: str,
    timestamp: int,
    properties: dict,
    user_properties: dict = None,
):
    """Forward an event to Amplitude analytics."""
    settings = get_settings()

    if not settings.amplitude_api_key:
        # Amplitude not configured, mark as forwarded anyway
        print(f"{YELLOW}[Amplitude] Skipped '{event_type}' - API key not configured{RESET}")
        await Collections.events().update_one(
            {"_id": event_id},
            {"$set": {"forwarded_to_amplitude": True}},
        )
        return

    amplitude_event = {
        "user_id": user_id,
        "event_type": event_type,
        "time": timestamp,
        "event_properties": properties,
    }

    if user_properties:
        amplitude_event["user_properties"] = {"$set": user_properties}

    print(f"{BLUE}[Amplitude] Sending '{event_type}' for user {user_id[:8]}...{RESET}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api2.amplitude.com/2/httpapi",
                json={
                    "api_key": settings.amplitude_api_key,
                    "events": [amplitude_event],
                },
                timeout=10.0,
            )

            success = response.status_code == 200

            if success:
                print(f"{GREEN}[Amplitude] ✓ Sent '{event_type}' successfully{RESET}")
            else:
                print(f"{RED}[Amplitude] ✗ Failed '{event_type}' - HTTP {response.status_code}: {response.text[:100]}{RESET}")

            await Collections.events().update_one(
                {"_id": event_id},
                {"$set": {"forwarded_to_amplitude": success}},
            )

    except Exception as e:
        print(f"{RED}[Amplitude] ✗ Error sending '{event_type}': {e}{RESET}")
        await Collections.events().update_one(
            {"_id": event_id},
            {"$set": {"forwarded_to_amplitude": False}},
        )


async def update_amplitude_user_properties(user_id: str, properties: dict):
    """Update user properties in Amplitude."""
    settings = get_settings()

    if not settings.amplitude_api_key:
        print(f"{YELLOW}[Amplitude] Skipped user properties update - API key not configured{RESET}")
        return

    print(f"{BLUE}[Amplitude] Updating user properties for {user_id[:8]}...{RESET}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api2.amplitude.com/2/httpapi",
                json={
                    "api_key": settings.amplitude_api_key,
                    "events": [
                        {
                            "user_id": user_id,
                            "event_type": "$identify",
                            "user_properties": {"$set": properties},
                        }
                    ],
                },
                timeout=10.0,
            )
            if response.status_code == 200:
                print(f"{GREEN}[Amplitude] ✓ Updated user properties{RESET}")
            else:
                print(f"{RED}[Amplitude] ✗ Failed to update user properties - HTTP {response.status_code}{RESET}")
    except Exception as e:
        print(f"{RED}[Amplitude] ✗ Error updating user properties: {e}{RESET}")


async def fetch_event_segmentation(
    event_type: str,
    start: str,
    end: str,
    interval: int = 1,
    metric: str = "totals",
) -> dict:
    """Fetch event segmentation data from Amplitude Data API."""
    settings = get_settings()

    if not settings.amplitude_api_key or not settings.amplitude_secret_key:
        raise ValueError("Amplitude API key or secret key not configured")

    params = {
        "e": json.dumps({"event_type": event_type}),
        "start": start,
        "end": end,
        "i": interval,
        "m": metric,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://amplitude.com/api/2/events/segmentation",
            params=params,
            auth=(settings.amplitude_api_key, settings.amplitude_secret_key),
            timeout=20.0,
        )
        response.raise_for_status()
        return response.json()


async def fetch_user_activity(user_id: str) -> dict:
    """
    Fetch a specific user's activity summary from Amplitude.
    Returns event counts, session data, and user properties.
    """
    settings = get_settings()

    if not settings.amplitude_api_key or not settings.amplitude_secret_key:
        raise ValueError("Amplitude API key or secret key not configured")

    print(f"{BLUE}[Amplitude] Fetching activity for user {user_id[:8]}...{RESET}")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://amplitude.com/api/2/useractivity",
            params={"user": user_id},
            auth=(settings.amplitude_api_key, settings.amplitude_secret_key),
            timeout=20.0,
        )
        
        if response.status_code == 200:
            print(f"{GREEN}[Amplitude] ✓ Fetched user activity{RESET}")
            return response.json()
        else:
            print(f"{RED}[Amplitude] ✗ Failed to fetch user activity - HTTP {response.status_code}{RESET}")
            return {}


async def fetch_user_event_counts(user_id: str, event_types: list[str] = None) -> dict:
    """
    Get event counts for a specific user from local MongoDB.
    This is faster than querying Amplitude and always available.
    
    Returns:
        {
            "test_cases_ran": 15,
            "task_submitted": 5,
            "proctoring_violation": 0,
            ...
        }
    """
    from db.collections import Collections
    
    query = {"user_id": user_id}
    if event_types:
        query["event_type"] = {"$in": event_types}
    
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
    ]
    
    cursor = Collections.events().aggregate(pipeline)
    results = await cursor.to_list(length=100)
    
    return {item["_id"]: item["count"] for item in results}


async def get_passport_analytics(user_id: str) -> dict:
    """
    Get comprehensive analytics for a user's skill passport.
    Combines local MongoDB data with Amplitude insights.
    
    Returns metrics useful for the passport:
    - Total test runs, submissions, pass rate
    - AI assistance usage (hints, chat)
    - Session statistics
    - Integrity indicators
    - Learning behavior patterns
    """
    from db.collections import Collections
    
    # Get all event counts
    event_counts = await fetch_user_event_counts(user_id)
    
    # Get session statistics
    sessions = await Collections.sessions().find({
        "user_id": user_id,
        "submitted": True,
    }).to_list(length=100)
    
    total_sessions = len(sessions)
    passed_sessions = sum(1 for s in sessions if s.get("passed", False))
    
    # Get average scores
    scores = [s.get("score", 0) for s in sessions if s.get("score") is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Get violation count
    violations = await Collections.events().count_documents({
        "user_id": user_id,
        "event_type": "proctoring_violation",
    })
    
    # Get AI chat message count
    chat_messages = await Collections.chat_messages().count_documents({
        "user_id": user_id,
        "role": "user",
    })
    
    # Calculate derived metrics
    test_runs = event_counts.get("test_cases_ran", 0)
    submissions = event_counts.get("task_submitted", 0)
    hints_requested = event_counts.get("contextual_hint_shown", 0)
    hint_acknowledged = event_counts.get("hint_acknowledged", 0)
    chat_help_requests = event_counts.get("chat_help_requested", 0)
    code_changes = event_counts.get("code_changed", 0)
    errors_encountered = event_counts.get("error_emitted", 0)
    fixes_applied = event_counts.get("fix_applied", 0)
    
    # Calculate AI reliance score (lower = more independent)
    total_actions = test_runs + submissions + code_changes
    ai_assists = hints_requested + chat_help_requests
    ai_reliance = ai_assists / total_actions if total_actions > 0 else 0
    
    # Calculate learning efficiency (how quickly they fix errors)
    fix_efficiency = fixes_applied / errors_encountered if errors_encountered > 0 else 1.0
    
    return {
        "user_id": user_id,
        "event_summary": event_counts,
        "session_stats": {
            "total_sessions": total_sessions,
            "passed_sessions": passed_sessions,
            "pass_rate": passed_sessions / total_sessions if total_sessions > 0 else 0,
            "average_score": round(avg_score, 1),
        },
        "activity_metrics": {
            "total_test_runs": test_runs,
            "total_submissions": submissions,
            "runs_per_submission": round(test_runs / submissions, 1) if submissions > 0 else 0,
            "code_changes": code_changes,
        },
        "ai_assistance_metrics": {
            "hints_requested": hints_requested,
            "hints_acknowledged": hint_acknowledged,
            "chat_messages_sent": chat_messages,
            "chat_help_requests": chat_help_requests,
            "ai_reliance_score": round(ai_reliance, 3),  # 0 = independent, 1 = heavily reliant
        },
        "learning_metrics": {
            "errors_encountered": errors_encountered,
            "fixes_applied": fixes_applied,
            "fix_efficiency": round(min(fix_efficiency, 1.0), 2),  # Cap at 1.0
        },
        "integrity_metrics": {
            "violations": violations,
            "integrity_score": max(0, 1.0 - (violations * 0.1)),  # -10% per violation
        },
    }
