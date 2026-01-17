#!/usr/bin/env python3
"""
Generate synthetic behavioral events for demo purposes.
Usage: python scripts/generate_events.py
"""

import asyncio
import os
import random
from datetime import datetime, timedelta
from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorClient


MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "proof_of_skill")


EVENT_TYPES = [
    "session_started",
    "editor_command",
    "code_changed",
    "run_attempted",
    "error_emitted",
    "fix_applied",
    "task_submitted",
    "session_ended",
]

EDITOR_COMMANDS = [
    "format_document",
    "save_attempt",
    "find",
    "undo",
    "redo",
    "comment",
    "uncomment",
    "go_to_definition",
]


def generate_session_events(user_id: str, session_id: str, task_id: str, archetype: str):
    """Generate a realistic sequence of events for a coding session."""
    events = []
    base_time = datetime.utcnow() - timedelta(hours=random.randint(1, 48))

    # Session characteristics based on archetype
    if archetype == "fast_iterator":
        run_count = random.randint(8, 15)
        error_rate = 0.4
        shortcut_ratio = 0.7
    elif archetype == "careful_tester":
        run_count = random.randint(3, 6)
        error_rate = 0.2
        shortcut_ratio = 0.5
    elif archetype == "debugger":
        run_count = random.randint(5, 10)
        error_rate = 0.5
        shortcut_ratio = 0.6
    elif archetype == "craftsman":
        run_count = random.randint(4, 7)
        error_rate = 0.25
        shortcut_ratio = 0.8
    else:
        run_count = random.randint(4, 10)
        error_rate = 0.35
        shortcut_ratio = 0.5

    current_time = base_time

    # Session started
    events.append({
        "_id": str(ObjectId()),
        "user_id": user_id,
        "session_id": session_id,
        "task_id": task_id,
        "event_type": "session_started",
        "timestamp": current_time,
        "properties": {
            "task_id": task_id,
            "difficulty": "easy",
        },
        "forwarded_to_amplitude": False,
        "processed_for_ml": False,
    })

    # Generate coding events
    for i in range(run_count):
        # Some editor commands
        num_commands = random.randint(2, 8)
        for _ in range(num_commands):
            current_time += timedelta(seconds=random.randint(3, 30))
            command = random.choice(EDITOR_COMMANDS)
            source = "shortcut" if random.random() < shortcut_ratio else "menu"

            events.append({
                "_id": str(ObjectId()),
                "user_id": user_id,
                "session_id": session_id,
                "task_id": task_id,
                "event_type": "editor_command",
                "timestamp": current_time,
                "properties": {
                    "command": command,
                    "source": source,
                },
                "forwarded_to_amplitude": False,
                "processed_for_ml": False,
            })

        # Code changes
        current_time += timedelta(seconds=random.randint(10, 60))
        events.append({
            "_id": str(ObjectId()),
            "user_id": user_id,
            "session_id": session_id,
            "task_id": task_id,
            "event_type": "code_changed",
            "timestamp": current_time,
            "properties": {
                "lines_changed": random.randint(1, 10),
                "chars_added": random.randint(-50, 200),
            },
            "forwarded_to_amplitude": False,
            "processed_for_ml": False,
        })

        # Run attempt
        current_time += timedelta(seconds=random.randint(5, 20))
        has_error = random.random() < error_rate
        tests_passed = 0 if has_error else random.randint(1, 4)

        events.append({
            "_id": str(ObjectId()),
            "user_id": user_id,
            "session_id": session_id,
            "task_id": task_id,
            "event_type": "run_attempted",
            "timestamp": current_time,
            "properties": {
                "result": "fail" if has_error else "pass",
                "runtime_ms": random.randint(50, 500),
                "tests_passed": tests_passed,
                "tests_total": 4,
            },
            "forwarded_to_amplitude": False,
            "processed_for_ml": False,
        })

        # Error and fix cycle
        if has_error:
            current_time += timedelta(seconds=random.randint(1, 5))
            error_type = random.choice(["TypeError", "SyntaxError", "ReferenceError", "RangeError"])

            events.append({
                "_id": str(ObjectId()),
                "user_id": user_id,
                "session_id": session_id,
                "task_id": task_id,
                "event_type": "error_emitted",
                "timestamp": current_time,
                "properties": {
                    "error_type": error_type,
                    "stack_depth": random.randint(1, 5),
                    "is_repeat": random.random() < 0.2,
                },
                "forwarded_to_amplitude": False,
                "processed_for_ml": False,
            })

            # Fix applied
            current_time += timedelta(seconds=random.randint(10, 120))
            events.append({
                "_id": str(ObjectId()),
                "user_id": user_id,
                "session_id": session_id,
                "task_id": task_id,
                "event_type": "fix_applied",
                "timestamp": current_time,
                "properties": {
                    "from_error_type": error_type,
                    "time_since_error_ms": random.randint(10000, 120000),
                },
                "forwarded_to_amplitude": False,
                "processed_for_ml": False,
            })

    # Task submitted
    current_time += timedelta(seconds=random.randint(5, 30))
    events.append({
        "_id": str(ObjectId()),
        "user_id": user_id,
        "session_id": session_id,
        "task_id": task_id,
        "event_type": "task_submitted",
        "timestamp": current_time,
        "properties": {
            "passed": True,
            "score": random.randint(75, 100),
        },
        "forwarded_to_amplitude": False,
        "processed_for_ml": False,
    })

    # Session ended
    current_time += timedelta(seconds=random.randint(1, 5))
    events.append({
        "_id": str(ObjectId()),
        "user_id": user_id,
        "session_id": session_id,
        "task_id": task_id,
        "event_type": "session_ended",
        "timestamp": current_time,
        "properties": {
            "duration_ms": int((current_time - base_time).total_seconds() * 1000),
            "outcome": "submitted",
        },
        "forwarded_to_amplitude": False,
        "processed_for_ml": False,
    })

    return events


async def main():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    print("=== Generating Synthetic Events ===\n")

    # Get demo users
    users = await db.users.find({"role": "candidate"}).to_list(length=100)

    if not users:
        print("No candidate users found. Run seed_demo_data.py first.")
        return

    task_ids = ["bugfix-null-check", "refactor-extract-function", "implement-debounce"]
    total_events = 0

    for user in users:
        user_id = str(user["_id"])
        archetype = user.get("archetype", "explorer")

        # Generate 2-4 sessions per user
        num_sessions = random.randint(2, 4)

        for i in range(num_sessions):
            session_id = f"synth-{user_id[:8]}-{i}"
            task_id = random.choice(task_ids)

            events = generate_session_events(user_id, session_id, task_id, archetype)

            # Insert events
            if events:
                await db.events.insert_many(events)
                total_events += len(events)

        print(f"  Generated events for: {user.get('email')} ({archetype})")

    print(f"\n=== Generated {total_events} total events ===")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
