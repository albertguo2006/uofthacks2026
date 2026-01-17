#!/usr/bin/env python3
"""
Seed tasks from JSON files into MongoDB.
Usage: python scripts/seed_tasks.py
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient


MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "proof_of_skill")
DATA_DIR = Path(__file__).parent.parent / "data"


async def seed_tasks():
    """Load and seed task definitions from JSON files."""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    tasks_dir = DATA_DIR / "tasks"

    if not tasks_dir.exists():
        print(f"Tasks directory not found: {tasks_dir}")
        return

    task_files = list(tasks_dir.glob("*.json"))
    print(f"Found {len(task_files)} task files")

    for task_file in task_files:
        with open(task_file) as f:
            task = json.load(f)

        task["created_at"] = datetime.utcnow()

        # Upsert task
        result = await db.tasks.update_one(
            {"task_id": task["task_id"]},
            {"$set": task},
            upsert=True,
        )

        if result.upserted_id:
            print(f"  Created: {task['task_id']}")
        else:
            print(f"  Updated: {task['task_id']}")

    print(f"\nSeeded {len(task_files)} tasks")
    client.close()


async def seed_jobs():
    """Load and seed job definitions from JSON file."""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    jobs_file = DATA_DIR / "jobs.json"

    if not jobs_file.exists():
        print(f"Jobs file not found: {jobs_file}")
        return

    with open(jobs_file) as f:
        jobs = json.load(f)

    print(f"Found {len(jobs)} jobs")

    for job in jobs:
        job["created_at"] = datetime.utcnow()

        result = await db.jobs.update_one(
            {"job_id": job["job_id"]},
            {"$set": job},
            upsert=True,
        )

        if result.upserted_id:
            print(f"  Created: {job['job_id']}")
        else:
            print(f"  Updated: {job['job_id']}")

    print(f"\nSeeded {len(jobs)} jobs")
    client.close()


async def main():
    print("=== Seeding Tasks ===")
    await seed_tasks()

    print("\n=== Seeding Jobs ===")
    await seed_jobs()

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
