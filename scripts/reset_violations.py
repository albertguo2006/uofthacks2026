#!/usr/bin/env python3
"""
Reset proctoring violations for a specific user.
Usage: python scripts/reset_violations.py
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "candid_data")


async def reset_violations_for_user(display_name: str):
    """Reset proctoring violations and integrity metrics for a user by display name."""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    print(f"Looking for user: {display_name}")

    # Find user by display name (case-insensitive)
    user = await db.users.find_one({
        "display_name": {"$regex": f"^{display_name}$", "$options": "i"}
    })

    if not user:
        # Try partial match
        user = await db.users.find_one({
            "display_name": {"$regex": display_name, "$options": "i"}
        })

    if not user:
        print(f"User '{display_name}' not found.")
        print("\nExisting users:")
        async for u in db.users.find({}, {"display_name": 1, "_id": 1}):
            print(f"  - {u.get('display_name', 'N/A')} ({u['_id']})")
        client.close()
        return False

    user_id = user["_id"]
    print(f"Found user: {user.get('display_name')} (ID: {user_id})")

    # Reset integrity score in user document
    result = await db.users.update_one(
        {"_id": user_id},
        {"$set": {"integrity_score": 1.0}}
    )
    print(f"Updated user integrity score: {result.modified_count} document(s)")

    # Reset violations in proctoring_sessions
    result = await db.proctoring_sessions.update_many(
        {"user_id": user_id},
        {"$set": {"violations": [], "integrity_score": 1.0, "flagged_for_review": False}}
    )
    print(f"Reset proctoring sessions: {result.modified_count} document(s)")

    # Reset passport metrics
    result = await db.passports.update_one(
        {"user_id": user_id},
        {"$set": {"metrics.integrity": 1.0, "proctoring_metrics": None}}
    )
    print(f"Updated passport: {result.modified_count} document(s)")

    # Reset any analytics events related to violations
    result = await db.events.delete_many({
        "user_id": user_id,
        "event_type": "proctoring_violation"
    })
    print(f"Deleted violation events: {result.deleted_count} document(s)")

    print(f"\nSuccessfully reset violations for {display_name}")
    client.close()
    return True


async def main():
    # Reset violations for Albert Guo
    await reset_violations_for_user("Albert Guo")


if __name__ == "__main__":
    asyncio.run(main())
