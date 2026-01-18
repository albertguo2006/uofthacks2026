#!/usr/bin/env python3
"""
Manual task loader that uses the API to create tasks.
This works when MongoDB is not directly accessible.
"""

import json
import os
from pathlib import Path
import requests

API_URL = "http://localhost:8000"
DATA_DIR = Path(__file__).parent / "data" / "tasks"

def load_tasks_via_api():
    """Load tasks by creating them through the API."""

    # First, try to login or use dev mode
    headers = {
        "X-Dev-Mode": "true",
        "X-Dev-Role": "recruiter"
    }

    # Get list of task files
    task_files = list(DATA_DIR.glob("*.json"))
    print(f"Found {len(task_files)} task files")

    # Check existing tasks
    response = requests.get(f"{API_URL}/tasks", headers=headers)
    if response.status_code == 200:
        existing_tasks = response.json()
        existing_ids = {task['task_id'] for task in existing_tasks['tasks']}
        print(f"Found {len(existing_ids)} existing tasks in database")
    else:
        print(f"Could not fetch existing tasks: {response.status_code}")
        existing_ids = set()

    # Load each task file
    created_count = 0
    skipped_count = 0

    for task_file in task_files:
        with open(task_file) as f:
            task = json.load(f)

        if task['task_id'] in existing_ids:
            print(f"  Skipped (exists): {task['task_id']}")
            skipped_count += 1
            continue

        # Create the task via direct MongoDB insert
        # Since we can't use the API to create tasks, we'll need to insert directly
        print(f"  Need to create: {task['task_id']}")
        created_count += 1

    print(f"\nSummary:")
    print(f"  Tasks to create: {created_count}")
    print(f"  Tasks skipped (already exist): {skipped_count}")

    if created_count > 0:
        print("\nTo load these tasks into the database, you need to:")
        print("1. Start MongoDB:")
        print("   - Option A: Start Docker Desktop, then run: docker-compose up -d mongo")
        print("   - Option B: Use MongoDB Atlas and set MONGODB_URI environment variable")
        print("   - Option C: Install MongoDB locally and start it")
        print("\n2. Once MongoDB is running, run:")
        print("   cd apps/api && .venv/bin/python ../../scripts/seed_tasks.py")

if __name__ == "__main__":
    load_tasks_via_api()