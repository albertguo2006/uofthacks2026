#!/usr/bin/env python3
"""
Seed realistic demo data and clean up test users.
Usage: python scripts/seed_realistic_demo.py
"""

import asyncio
import os
from datetime import datetime, timedelta
import random

from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt


MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "proof_of_skill")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Realistic demo candidates with diverse backgrounds
DEMO_USERS = [
    {
        "_id": "cand-sarah-kim",
        "email": "sarah.kim@stanford.edu",
        "password": "demo2024",
        "display_name": "Sarah Kim",
        "role": "candidate",
        "archetype": "fast_iterator",
        "skill_vector": [0.88, 0.72, 0.65, 0.82, 0.94],
        "integrity_score": 0.94,
        "avatar_url": None,
    },
    {
        "_id": "cand-marcus-johnson",
        "email": "marcus.j@berkeley.edu",
        "password": "demo2024",
        "display_name": "Marcus Johnson",
        "role": "candidate",
        "archetype": "debugger",
        "skill_vector": [0.68, 0.91, 0.78, 0.85, 0.92],
        "integrity_score": 0.92,
        "avatar_url": None,
    },
    {
        "_id": "cand-priya-patel",
        "email": "priya.patel@mit.edu",
        "password": "demo2024",
        "display_name": "Priya Patel",
        "role": "candidate",
        "archetype": "careful_tester",
        "skill_vector": [0.62, 0.85, 0.89, 0.71, 0.97],
        "integrity_score": 0.97,
        "avatar_url": None,
    },
    {
        "_id": "cand-james-chen",
        "email": "jchen@uwaterloo.ca",
        "password": "demo2024",
        "display_name": "James Chen",
        "role": "candidate",
        "archetype": "craftsman",
        "skill_vector": [0.71, 0.78, 0.92, 0.88, 0.91],
        "integrity_score": 0.91,
        "avatar_url": None,
    },
    {
        "_id": "cand-emma-rodriguez",
        "email": "emma.rodriguez@gatech.edu",
        "password": "demo2024",
        "display_name": "Emma Rodriguez",
        "role": "candidate",
        "archetype": "explorer",
        "skill_vector": [0.82, 0.69, 0.74, 0.79, 0.89],
        "integrity_score": 0.89,
        "avatar_url": None,
    },
    {
        "_id": "cand-david-nguyen",
        "email": "david.nguyen@cmu.edu",
        "password": "demo2024",
        "display_name": "David Nguyen",
        "role": "candidate",
        "archetype": "fast_iterator",
        "skill_vector": [0.91, 0.65, 0.58, 0.76, 0.86],
        "integrity_score": 0.86,
        "avatar_url": None,
    },
    {
        "_id": "cand-olivia-williams",
        "email": "owilliams@utoronto.ca",
        "password": "demo2024",
        "display_name": "Olivia Williams",
        "role": "candidate",
        "archetype": "debugger",
        "skill_vector": [0.73, 0.88, 0.81, 0.84, 0.93],
        "integrity_score": 0.93,
        "avatar_url": None,
    },
    {
        "_id": "cand-alex-thompson",
        "email": "athompson@columbia.edu",
        "password": "demo2024",
        "display_name": "Alex Thompson",
        "role": "candidate",
        "archetype": "careful_tester",
        "skill_vector": [0.58, 0.82, 0.86, 0.67, 0.95],
        "integrity_score": 0.95,
        "avatar_url": None,
    },
    # Recruiter account
    {
        "_id": "recruiter-demo",
        "email": "recruiter@techcorp.com",
        "password": "demo2024",
        "display_name": "Taylor Morgan",
        "role": "recruiter",
    },
]


# Notable moments for each candidate
NOTABLE_MOMENTS = {
    "cand-sarah-kim": [
        {"type": "speed", "highlight": "Solved binary search optimization in 4 minutes", "task_id": "optimize-binary-search"},
        {"type": "achievement", "highlight": "Perfect score on algorithm challenge", "task_id": "implement-debounce"},
    ],
    "cand-marcus-johnson": [
        {"type": "debugging", "highlight": "Identified race condition in async code", "task_id": "bugfix-async-race"},
        {"type": "insight", "highlight": "Found memory leak in production code sample", "task_id": "bugfix-memory-leak"},
    ],
    "cand-priya-patel": [
        {"type": "quality", "highlight": "100% test coverage on feature implementation", "task_id": "implement-validation"},
        {"type": "thoroughness", "highlight": "Caught 3 edge cases before submission", "task_id": "refactor-extract-function"},
    ],
    "cand-james-chen": [
        {"type": "architecture", "highlight": "Elegant refactor reducing code by 40%", "task_id": "refactor-extract-function"},
        {"type": "maintainability", "highlight": "Outstanding code organization and naming", "task_id": "implement-cache"},
    ],
    "cand-emma-rodriguez": [
        {"type": "creative", "highlight": "Novel approach to graph traversal problem", "task_id": "implement-graph-traversal"},
        {"type": "innovation", "highlight": "Used recursive solution where others iterated", "task_id": "tree-manipulation"},
    ],
    "cand-david-nguyen": [
        {"type": "speed", "highlight": "Fastest completion time for medium difficulty", "task_id": "implement-debounce"},
        {"type": "iteration", "highlight": "5 rapid iterations to optimal solution", "task_id": "optimize-query"},
    ],
    "cand-olivia-williams": [
        {"type": "debugging", "highlight": "Systematic root cause analysis of null pointer", "task_id": "bugfix-null-check"},
        {"type": "precision", "highlight": "Zero wasted steps in debugging process", "task_id": "bugfix-off-by-one"},
    ],
    "cand-alex-thompson": [
        {"type": "quality", "highlight": "Wrote comprehensive test suite alongside solution", "task_id": "implement-validation"},
        {"type": "reliability", "highlight": "All edge cases handled in first submission", "task_id": "implement-pagination"},
    ],
}


async def cleanup_test_data(db):
    """Remove test users and related data."""
    print("Cleaning up test data...")

    # Find test users by patterns
    test_patterns = [
        {"email": {"$regex": "test", "$options": "i"}},
        {"email": {"$regex": "example.com", "$options": "i"}},
        {"display_name": {"$regex": "test", "$options": "i"}},
        {"_id": {"$regex": "demo-", "$options": "i"}},
        {"_id": {"$regex": "test", "$options": "i"}},
    ]

    deleted_users = []
    for pattern in test_patterns:
        users = await db.users.find(pattern).to_list(length=100)
        for user in users:
            user_id = user["_id"]
            if user_id not in deleted_users:
                # Delete related data
                await db.passports.delete_many({"user_id": user_id})
                await db.sessions.delete_many({"user_id": user_id})
                await db.events.delete_many({"user_id": user_id})
                await db.skill_proficiencies.delete_many({"user_id": user_id})
                await db.users.delete_one({"_id": user_id})
                deleted_users.append(user_id)
                print(f"  Removed: {user.get('email', user_id)}")

    if not deleted_users:
        print("  No test data found to remove")
    else:
        print(f"  Total removed: {len(deleted_users)} users")


async def seed_users(db):
    """Seed demo users."""
    print("\nSeeding realistic demo users...")

    for user_data in DEMO_USERS:
        user = {
            "_id": user_data["_id"],
            "email": user_data["email"],
            "display_name": user_data["display_name"],
            "role": user_data["role"],
            "password_hash": hash_password(user_data["password"]),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(7, 60)),
            "passkey_credentials": [],
        }

        # Add candidate-specific fields
        if user_data["role"] == "candidate":
            user["archetype"] = user_data.get("archetype")
            user["skill_vector"] = user_data.get("skill_vector")
            user["integrity_score"] = user_data.get("integrity_score")
            user["avatar_url"] = user_data.get("avatar_url")

        result = await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": user},
            upsert=True,
        )

        if result.upserted_id:
            print(f"  Created: {user['display_name']} ({user['email']})")
        else:
            print(f"  Updated: {user['display_name']} ({user['email']})")


async def seed_passports(db):
    """Seed passports for demo candidates."""
    print("\nSeeding skill passports...")

    candidate_users = [u for u in DEMO_USERS if u["role"] == "candidate"]

    for user in candidate_users:
        skill_vector = user.get("skill_vector", [0.5, 0.5, 0.5, 0.5, 0.5])

        # Build notable moments
        notable = []
        for moment in NOTABLE_MOMENTS.get(user["_id"], []):
            notable.append({
                "session_id": f"session-{user['_id']}-{len(notable)}",
                "task_id": moment["task_id"],
                "highlight": moment["highlight"],
                "timestamp": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                "type": moment["type"],
            })

        passport = {
            "_id": f"passport-{user['_id']}",
            "user_id": user["_id"],
            "display_name": user["display_name"],
            "archetype": user.get("archetype"),
            "archetype_confidence": random.uniform(0.78, 0.95),
            "skill_vector": skill_vector,
            "metrics": {
                "iteration_velocity": skill_vector[0],
                "debug_efficiency": skill_vector[1],
                "craftsmanship": skill_vector[2],
                "tool_fluency": skill_vector[3],
                "integrity": user.get("integrity_score", skill_vector[4]),
            },
            "sessions_completed": random.randint(4, 8),
            "tasks_passed": random.randint(3, 7),
            "notable_sessions": notable,
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
            print(f"  Created passport for: {user['display_name']}")
        else:
            print(f"  Updated passport for: {user['display_name']}")


async def seed_sessions(db):
    """Seed realistic sessions for demo candidates."""
    print("\nSeeding coding sessions...")

    candidate_users = [u for u in DEMO_USERS if u["role"] == "candidate"]
    task_ids = [
        "bugfix-null-check",
        "refactor-extract-function",
        "implement-debounce",
        "optimize-binary-search",
        "implement-validation",
        "bugfix-off-by-one",
    ]

    session_count = 0
    for user in candidate_users:
        # Create 4-7 sessions per user
        num_sessions = random.randint(4, 7)
        for i in range(num_sessions):
            task_id = random.choice(task_ids)

            # Higher pass rate for higher integrity users
            pass_chance = 0.7 + (user.get("integrity_score", 0.8) * 0.2)
            passed = random.random() < pass_chance
            score = random.randint(78, 100) if passed else random.randint(35, 65)

            # Session timing
            started = datetime.utcnow() - timedelta(
                days=random.randint(1, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            duration_minutes = random.randint(8, 45)
            ended = started + timedelta(minutes=duration_minutes)

            session = {
                "_id": f"session-{user['_id']}-{i}",
                "session_id": f"sess-{user['_id'][-8:]}-{i:02d}",
                "user_id": user["_id"],
                "task_id": task_id,
                "language": random.choice(["python", "javascript", "typescript"]),
                "started_at": started,
                "ended_at": ended,
                "duration_seconds": duration_minutes * 60,
                "submitted": True,
                "passed": passed,
                "score": score,
                "run_count": random.randint(3, 25),
                "error_count": random.randint(0, 8),
            }

            await db.sessions.update_one(
                {"_id": session["_id"]},
                {"$set": session},
                upsert=True,
            )
            session_count += 1

    print(f"  Created {session_count} sessions")


async def main():
    print("=" * 50)
    print("Realistic Demo Data Seeder")
    print("=" * 50)
    print(f"\nConnecting to: {DATABASE_NAME}")

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    await cleanup_test_data(db)
    await seed_users(db)
    await seed_passports(db)
    await seed_sessions(db)

    print("\n" + "=" * 50)
    print("Demo Data Seeded Successfully!")
    print("=" * 50)
    print("\nDemo Credentials (password: demo2024):")
    print("-" * 40)
    for user in DEMO_USERS:
        role_label = "Recruiter" if user["role"] == "recruiter" else f"Candidate ({user.get('archetype', 'N/A')})"
        print(f"  {user['display_name']}")
        print(f"    Email: {user['email']}")
        print(f"    Role:  {role_label}")
        print()

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
