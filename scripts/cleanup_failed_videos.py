#!/usr/bin/env python3
"""
Clean up failed videos from the database.

Deletes videos where:
- status is "failed"
- TwelveLabs video ID is missing (video not accessible from TwelveLabs)

Also cleans up:
- Associated passport references
- Local video files

Usage: python scripts/cleanup_failed_videos.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the api directory to path for imports
api_dir = Path(__file__).parent.parent / "apps" / "api"
sys.path.insert(0, str(api_dir))

# Load .env file from api directory
from dotenv import load_dotenv
env_path = api_dir / ".env"
load_dotenv(env_path)

from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "candid_data")


async def cleanup_failed_videos():
    """Delete all failed or inaccessible videos from the database."""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    print("=" * 60)
    print("Video Cleanup Script")
    print("=" * 60)

    # Find videos that are failed or don't have a TwelveLabs video ID
    # (meaning they can't be accessed from TwelveLabs)
    failed_query = {
        "$or": [
            {"status": "failed"},
            {
                "status": "ready",
                "twelvelabs_video_id": {"$in": [None, ""]},
            },
            {
                "status": {"$in": ["uploading", "indexing"]},
                # Videos stuck in uploading/indexing for too long (no twelvelabs_video_id)
                "twelvelabs_video_id": {"$in": [None, ""]},
            },
        ]
    }

    videos_to_delete = await db.videos.find(failed_query).to_list(length=1000)

    if not videos_to_delete:
        print("\nNo failed or inaccessible videos found.")
        client.close()
        return

    print(f"\nFound {len(videos_to_delete)} video(s) to delete:\n")

    deleted_count = 0
    passports_updated = 0
    files_deleted = 0

    for video in videos_to_delete:
        video_id = video.get("_id")
        user_id = video.get("user_id")
        status = video.get("status", "unknown")
        filename = video.get("filename", "unknown")
        twelvelabs_id = video.get("twelvelabs_video_id")
        uploaded_by = video.get("uploaded_by", "candidate")

        print(f"  - Video ID: {video_id}")
        print(f"    Status: {status}")
        print(f"    Filename: {filename}")
        print(f"    Candidate: {user_id}")
        print(f"    Uploaded by: {uploaded_by}")
        print(f"    TwelveLabs ID: {twelvelabs_id or 'MISSING'}")

        # Delete local file if it exists
        file_path = video.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"    Deleted file: {file_path}")
                files_deleted += 1
            except Exception as e:
                print(f"    Failed to delete file: {e}")

        # Delete from videos collection
        result = await db.videos.delete_one({"_id": video_id})
        if result.deleted_count > 0:
            deleted_count += 1
            print(f"    Deleted from database")

        # Clean up passport reference if this was the interview video
        if user_id:
            passport_result = await db.passports.update_one(
                {"user_id": user_id, "interview_video_id": video_id},
                {
                    "$set": {
                        "interview_video_id": None,
                        "interview_highlights": [],
                        "interview_summary": None,
                        "communication_scores": None,
                    }
                },
            )
            if passport_result.modified_count > 0:
                passports_updated += 1
                print(f"    Cleared passport reference")

        print()

    print("=" * 60)
    print("Summary:")
    print(f"  Videos deleted: {deleted_count}")
    print(f"  Passports updated: {passports_updated}")
    print(f"  Files deleted: {files_deleted}")
    print("=" * 60)

    client.close()


async def main():
    await cleanup_failed_videos()


if __name__ == "__main__":
    asyncio.run(main())
