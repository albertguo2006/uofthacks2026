#!/usr/bin/env python3
"""
Seed demo data including sample users, passports, and sessions.
Usage: python scripts/seed_demo_data.py
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext


MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "proof_of_skill")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


DEMO_USERS = [
    {
        "_id": "demo-candidate-1",
        "email": "alice@example.com",
        "password": "password123",
        "display_name": "Alice Chen",
        "role": "candidate",
        "archetype": "fast_iterator",
        "skill_vector": [0.75, 0.6, 0.5, 0.7, 0.9],
        "integrity_score": 0.9,
    },
    {
        "_id": "demo-candidate-2",
        "email": "bob@example.com",
        "password": "password123",
        "display_name": "Bob Martinez",
        "role": "candidate",
        "archetype": "careful_tester",
        "skill_vector": [0.5, 0.8, 0.75, 0.6, 0.95],
        "integrity_score": 0.95,
    },
    {
        "_id": "demo-candidate-3",
        "email": "carol@example.com",
        "password": "password123",
        "display_name": "Carol Williams",
        "role": "candidate",
        "archetype": "debugger",
        "skill_vector": [0.6, 0.85, 0.6, 0.7, 0.88],
        "integrity_score": 0.88,
    },
    {
        "_id": "demo-recruiter-1",
        "email": "recruiter@example.com",
        "password": "password123",
        "display_name": "Demo Recruiter",
        "role": "recruiter",
    },
]


async def seed_users(db):
    """Seed demo users."""
    print("Seeding users...")

    for user_data in DEMO_USERS:
        user = {
            **user_data,
            "password_hash": pwd_context.hash(user_data["password"]),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            "passkey_credentials": [],
        }
        del user["password"]

        result = await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": user},
            upsert=True,
        )

        if result.upserted_id:
            print(f"  Created: {user['email']}")
        else:
            print(f"  Updated: {user['email']}")


async def seed_passports(db):
    """Seed passports for demo candidates."""
    print("\nSeeding passports...")

    candidate_users = [u for u in DEMO_USERS if u["role"] == "candidate"]

    for user in candidate_users:
        passport = {
            "_id": f"passport-{user['_id']}",
            "user_id": user["_id"],
            "archetype": user.get("archetype"),
            "archetype_confidence": random.uniform(0.7, 0.95),
            "skill_vector": user.get("skill_vector", []),
            "metrics": {
                "iteration_velocity": user.get("skill_vector", [0])[0] if user.get("skill_vector") else 0,
                "debug_efficiency": user.get("skill_vector", [0, 0])[1] if len(user.get("skill_vector", [])) > 1 else 0,
                "craftsmanship": user.get("skill_vector", [0, 0, 0])[2] if len(user.get("skill_vector", [])) > 2 else 0,
                "tool_fluency": user.get("skill_vector", [0, 0, 0, 0])[3] if len(user.get("skill_vector", [])) > 3 else 0,
                "integrity": user.get("integrity_score", 1.0),
            },
            "notable_sessions": [
                {
                    "session_id": f"session-{user['_id']}-1",
                    "task_id": "bugfix-null-check",
                    "highlight": "Fixed null check bug in under 2 minutes",
                    "timestamp": datetime.utcnow() - timedelta(days=5),
                    "type": "achievement",
                },
            ],
            "interview_video_id": None,
            "interview_highlights": [],
            "updated_at": datetime.utcnow(),
        }

        result = await db.passports.update_one(
            {"user_id": user["_id"]},
            {"$set": passport},
            upsert=True,
        )

        if result.upserted_id:
            print(f"  Created passport for: {user['email']}")
        else:
            print(f"  Updated passport for: {user['email']}")


async def seed_sessions(db):
    """Seed sample sessions for demo candidates."""
    print("\nSeeding sessions...")

    candidate_users = [u for u in DEMO_USERS if u["role"] == "candidate"]
    task_ids = ["bugfix-null-check", "refactor-extract-function", "implement-debounce"]

    session_count = 0
    for user in candidate_users:
        # Create 3-5 sessions per user
        num_sessions = random.randint(3, 5)
        for i in range(num_sessions):
            task_id = random.choice(task_ids)
            passed = random.random() > 0.2  # 80% pass rate
            score = random.randint(80, 100) if passed else random.randint(40, 70)

            session = {
                "_id": f"session-{user['_id']}-{i}",
                "session_id": f"sess-{user['_id'][:8]}-{i}",
                "user_id": user["_id"],
                "task_id": task_id,
                "started_at": datetime.utcnow() - timedelta(days=random.randint(1, 14), hours=random.randint(0, 23)),
                "ended_at": datetime.utcnow() - timedelta(days=random.randint(1, 14)),
                "submitted": True,
                "passed": passed,
                "score": score,
            }

            await db.sessions.update_one(
                {"_id": session["_id"]},
                {"$set": session},
                upsert=True,
            )
            session_count += 1

    print(f"  Created {session_count} sessions")


async def main():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    print("=== Seeding Demo Data ===\n")

    await seed_users(db)
    await seed_passports(db)
    await seed_sessions(db)

    # Also seed tasks and jobs
    print("\n=== Seeding Tasks and Jobs ===")
    from seed_tasks import seed_tasks, seed_jobs
    await seed_tasks()
    await seed_jobs()

    print("\n=== Demo Data Seeded Successfully ===")
    print("\nDemo Credentials:")
    for user in DEMO_USERS:
        print(f"  {user['email']} / password123 ({user['role']})")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
