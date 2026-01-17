#!/usr/bin/env python3
"""
Migration script to convert task JSON files from v1 to v2 format.

V1 format:
- language: str
- starter_code: str

V2 format:
- languages: list[str]
- starter_codes: dict[str, str]
- proctored: bool
- tags: list[str]
"""

import json
import os
from pathlib import Path

# Task directory
TASKS_DIR = Path(__file__).parent.parent / "data" / "tasks"

# Tag suggestions based on task content
TAG_KEYWORDS = {
    "array": "arrays",
    "list": "arrays",
    "string": "strings",
    "null": "null-handling",
    "undefined": "null-handling",
    "async": "async",
    "promise": "async",
    "race": "async",
    "debounce": "optimization",
    "throttle": "optimization",
    "cache": "optimization",
    "memoiz": "memoization",
    "recursive": "recursion",
    "recursion": "recursion",
    "loop": "iteration",
    "validation": "validation",
    "input": "validation",
    "refactor": "refactoring",
    "extract": "refactoring",
    "function": "functions",
    "index": "arrays",
    "error": "error-handling",
    "bug": "debugging",
    "fix": "debugging",
    "pointer": "pointers",
    "dynamic": "dynamic-programming",
    "dp": "dynamic-programming",
}


def suggest_tags(task: dict) -> list[str]:
    """Suggest tags based on task content."""
    tags = set()

    # Check title and description for keywords
    text = (task.get("title", "") + " " + task.get("description", "")).lower()

    for keyword, tag in TAG_KEYWORDS.items():
        if keyword in text:
            tags.add(tag)

    # Add category-based tag
    category = task.get("category", "")
    if category == "bugfix":
        tags.add("debugging")
    elif category == "refactor":
        tags.add("refactoring")
    elif category == "optimization":
        tags.add("optimization")

    return list(tags)[:5]  # Limit to 5 tags


def migrate_task(task: dict) -> dict:
    """Migrate a single task from v1 to v2 format."""
    # Already migrated?
    if "languages" in task and "starter_codes" in task:
        print(f"  Task already migrated: {task.get('task_id')}")
        return task

    # Get old values
    language = task.get("language", "javascript")
    starter_code = task.get("starter_code", "")

    # Create new format
    migrated = {
        **task,
        "languages": [language],
        "starter_codes": {language: starter_code},
        "proctored": task.get("proctored", False),
        "tags": task.get("tags", suggest_tags(task)),
    }

    # Remove old fields
    if "language" in migrated:
        del migrated["language"]
    if "starter_code" in migrated:
        del migrated["starter_code"]

    return migrated


def migrate_all_tasks():
    """Migrate all task JSON files."""
    if not TASKS_DIR.exists():
        print(f"Tasks directory not found: {TASKS_DIR}")
        return

    task_files = list(TASKS_DIR.glob("*.json"))
    print(f"Found {len(task_files)} task files to migrate")

    for task_file in task_files:
        print(f"\nMigrating: {task_file.name}")

        try:
            with open(task_file, "r") as f:
                task = json.load(f)

            migrated = migrate_task(task)

            with open(task_file, "w") as f:
                json.dump(migrated, f, indent=2)

            print(f"  Migrated successfully")
            print(f"  - Languages: {migrated['languages']}")
            print(f"  - Tags: {migrated['tags']}")

        except Exception as e:
            print(f"  Error: {e}")

    print(f"\n{'='*50}")
    print("Migration complete!")
    print("Run 'python scripts/seed_tasks.py' to re-seed the database")


def add_proctored_task_example():
    """Add an example proctored task for testing."""
    example_task = {
        "task_id": "proctored-two-sum",
        "title": "Two Sum Challenge",
        "description": "## Problem\n\nGiven an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.\n\n## Requirements\n\n1. Each input would have exactly one solution\n2. You may not use the same element twice\n3. You can return the answer in any order\n\n## Example\n\n```\nInput: nums = [2, 7, 11, 15], target = 9\nOutput: [0, 1]\nExplanation: Because nums[0] + nums[1] == 9, we return [0, 1].\n```",
        "difficulty": "easy",
        "category": "feature",
        "languages": ["python", "javascript"],
        "starter_codes": {
            "python": "def two_sum(nums, target):\n    # Your code here\n    pass\n",
            "javascript": "function twoSum(nums, target) {\n  // Your code here\n}\n\nmodule.exports = { twoSum };"
        },
        "solution_code": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []",
        "test_cases": [
            {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected_output": [0, 1], "hidden": False},
            {"input": {"nums": [3, 2, 4], "target": 6}, "expected_output": [1, 2], "hidden": False},
            {"input": {"nums": [3, 3], "target": 6}, "expected_output": [0, 1], "hidden": True}
        ],
        "time_limit_seconds": 5,
        "proctored": True,
        "tags": ["arrays", "hash-table", "two-pointers"]
    }

    task_file = TASKS_DIR / "proctored-two-sum.json"
    with open(task_file, "w") as f:
        json.dump(example_task, f, indent=2)

    print(f"\nCreated example proctored task: {task_file}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--add-example":
        add_proctored_task_example()
    else:
        migrate_all_tasks()

        # Ask if user wants to add example proctored task
        print("\nWould you like to add an example proctored task? (y/n)")
        try:
            response = input().strip().lower()
            if response == "y":
                add_proctored_task_example()
        except:
            pass
