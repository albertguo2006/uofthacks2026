import httpx
import os
from datetime import datetime
from config import get_settings
from db.collections import Collections

TWELVELABS_API_URL = "https://api.twelvelabs.io/v1.2"


async def get_or_create_index() -> str:
    """Get or create a TwelveLabs index for the application."""
    settings = get_settings()

    if not settings.twelvelabs_api_key:
        return None

    headers = {
        "x-api-key": settings.twelvelabs_api_key,
        "Content-Type": "application/json",
    }

    index_name = "proof-of-skill-interviews"

    try:
        async with httpx.AsyncClient() as client:
            # List existing indexes
            response = await client.get(
                f"{TWELVELABS_API_URL}/indexes",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code == 200:
                indexes = response.json().get("data", [])
                for index in indexes:
                    if index["index_name"] == index_name:
                        return index["_id"]

            # Create new index
            response = await client.post(
                f"{TWELVELABS_API_URL}/indexes",
                headers=headers,
                json={
                    "index_name": index_name,
                    "engines": [
                        {
                            "engine_name": "marengo2.6",
                            "engine_options": ["visual", "conversation", "text_in_video"],
                        },
                        {
                            "engine_name": "pegasus1.1",
                            "engine_options": ["visual", "conversation"],
                        },
                    ],
                },
                timeout=30.0,
            )

            if response.status_code in [200, 201]:
                return response.json().get("_id")

            print(f"Failed to create TwelveLabs index: {response.text}")
            return None

    except Exception as e:
        print(f"TwelveLabs index error: {e}")
        return None


async def upload_video_to_twelvelabs(
    video_id: str,
    user_id: str,
    file_path: str,
):
    """Upload and index a video in TwelveLabs."""
    settings = get_settings()

    if not settings.twelvelabs_api_key:
        # TwelveLabs not configured
        await Collections.videos().update_one(
            {"_id": video_id},
            {"$set": {"status": "ready"}},  # Mark as ready without actual processing
        )
        return

    try:
        # Update status
        await Collections.videos().update_one(
            {"_id": video_id},
            {"$set": {"status": "indexing"}},
        )

        # Get or create index
        index_id = await get_or_create_index()
        if not index_id:
            await Collections.videos().update_one(
                {"_id": video_id},
                {"$set": {"status": "failed"}},
            )
            return

        headers = {
            "x-api-key": settings.twelvelabs_api_key,
        }

        async with httpx.AsyncClient() as client:
            # Upload video
            with open(file_path, "rb") as f:
                files = {"video_file": (os.path.basename(file_path), f, "video/mp4")}
                data = {"index_id": index_id}

                response = await client.post(
                    f"{TWELVELABS_API_URL}/tasks",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=300.0,  # 5 minutes for upload
                )

            if response.status_code not in [200, 201]:
                print(f"TwelveLabs upload failed: {response.text}")
                await Collections.videos().update_one(
                    {"_id": video_id},
                    {"$set": {"status": "failed"}},
                )
                return

            result = response.json()
            task_id = result.get("_id")
            twelvelabs_video_id = result.get("video_id")

            # Update with TwelveLabs IDs
            await Collections.videos().update_one(
                {"_id": video_id},
                {
                    "$set": {
                        "twelvelabs_index_id": index_id,
                        "twelvelabs_video_id": twelvelabs_video_id,
                        "twelvelabs_task_id": task_id,
                        "status": "indexing",
                    }
                },
            )

            # Poll for completion (in production, use webhooks)
            for _ in range(60):  # Max 5 minutes
                await asyncio.sleep(5)

                status_response = await client.get(
                    f"{TWELVELABS_API_URL}/tasks/{task_id}",
                    headers=headers,
                    timeout=30.0,
                )

                if status_response.status_code == 200:
                    task_status = status_response.json().get("status")
                    if task_status == "ready":
                        await Collections.videos().update_one(
                            {"_id": video_id},
                            {
                                "$set": {
                                    "status": "ready",
                                    "ready_at": datetime.utcnow(),
                                }
                            },
                        )

                        # Update passport with video
                        await Collections.passports().update_one(
                            {"user_id": user_id},
                            {"$set": {"interview_video_id": video_id}},
                        )

                        # Clean up temp file
                        if os.path.exists(file_path):
                            os.remove(file_path)

                        return

                    elif task_status == "failed":
                        await Collections.videos().update_one(
                            {"_id": video_id},
                            {"$set": {"status": "failed"}},
                        )
                        return

            # Timeout
            await Collections.videos().update_one(
                {"_id": video_id},
                {"$set": {"status": "failed"}},
            )

    except Exception as e:
        print(f"TwelveLabs upload error: {e}")
        await Collections.videos().update_one(
            {"_id": video_id},
            {"$set": {"status": "failed"}},
        )


async def search_video(twelvelabs_video_id: str, query: str) -> list[dict]:
    """Search a video for specific moments."""
    settings = get_settings()

    if not settings.twelvelabs_api_key or not twelvelabs_video_id:
        return []

    headers = {
        "x-api-key": settings.twelvelabs_api_key,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TWELVELABS_API_URL}/search",
                headers=headers,
                json={
                    "query": query,
                    "index_id": await get_or_create_index(),
                    "search_options": ["visual", "conversation"],
                    "filter": {"id": [twelvelabs_video_id]},
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                print(f"TwelveLabs search failed: {response.text}")
                return []

            results = response.json().get("data", [])

            return [
                {
                    "start_time": r.get("start", 0),
                    "end_time": r.get("end", 0),
                    "confidence": r.get("confidence", 0),
                    "transcript": r.get("metadata", {}).get("text", ""),
                }
                for r in results
            ]

    except Exception as e:
        print(f"TwelveLabs search error: {e}")
        return []


# Import asyncio for the polling loop
import asyncio
