"""
TwelveLabs Video Intelligence Service

Provides interview video analysis capabilities:
- Video indexing with Marengo engine
- Semantic search within videos
- Interview summary generation with Pegasus
- Highlight clip extraction
- Communication style analysis
"""

import httpx
import asyncio
import os
import json
from datetime import datetime
from typing import Optional
from config import get_settings
from db.collections import Collections

TWELVELABS_API_URL = "https://api.twelvelabs.io/v1.3"


class TwelveLabsService:
    """
    TwelveLabs integration for interview video understanding.
    Uses Marengo for indexing and Pegasus for generation.
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.twelvelabs_api_key
        self.index_id = settings.twelvelabs_index_id

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict:
        """Make authenticated request to TwelveLabs API."""
        if not self.api_key:
            return {"error": "TwelveLabs API key not configured"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method,
                f"{TWELVELABS_API_URL}{endpoint}",
                headers={"x-api-key": self.api_key},
                **kwargs
            )
            response.raise_for_status()
            return response.json()

    async def get_or_create_index(self) -> Optional[str]:
        """Get or create a TwelveLabs index for the application."""
        if not self.api_key:
            return None

        # Use configured index if available
        if self.index_id:
            print(f"[TwelveLabs] Using pre-configured index: {self.index_id}")
            return self.index_id

        index_name = "skillpulse-interviews"

        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                }

                # List existing indexes
                print(f"[TwelveLabs] Checking for existing index '{index_name}'...")
                response = await client.get(
                    f"{TWELVELABS_API_URL}/indexes",
                    headers=headers,
                    timeout=30.0,
                )

                print(f"[TwelveLabs] List indexes response: {response.status_code}")
                if response.status_code == 200:
                    indexes = response.json().get("data", [])
                    for index in indexes:
                        if index.get("index_name") == index_name:
                            index_id = index.get("_id")
                            print(f"[TwelveLabs] Found existing index: {index_id}")
                            return index_id
                else:
                    print(f"[TwelveLabs] List indexes failed: {response.text}")

                # Create new index with v1.3 format
                print(f"[TwelveLabs] Creating new index '{index_name}'...")
                create_payload = {
                    "index_name": index_name,
                    "models": [
                        {
                            "model_name": "marengo2.7",
                            "model_options": ["visual", "audio"],
                        }
                    ],
                }
                print(f"[TwelveLabs] Create payload: {create_payload}")

                response = await client.post(
                    f"{TWELVELABS_API_URL}/indexes",
                    headers=headers,
                    json=create_payload,
                    timeout=30.0,
                )

                print(f"[TwelveLabs] Create index response: {response.status_code}")
                if response.status_code in [200, 201]:
                    result = response.json()
                    index_id = result.get("_id")
                    print(f"[TwelveLabs] Created new index: {index_id}")
                    return index_id

                print(f"[TwelveLabs] Failed to create index: {response.text}")
                return None

        except Exception as e:
            print(f"[TwelveLabs] Index error: {e}")
            return None

    async def index_interview_video(
        self,
        video_url: str,
        user_id: str,
        session_id: str
    ) -> dict:
        """
        Upload and index an interview recording.
        Returns task_id for polling status.
        """
        index_id = await self.get_or_create_index()
        if not index_id:
            return {"error": "Failed to get or create index"}

        try:
            result = await self._request(
                "POST",
                "/tasks",
                json={
                    "index_id": index_id,
                    "url": video_url,
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "type": "coding_interview",
                    },
                },
            )
            return {
                "task_id": result.get("_id"),
                "status": result.get("status"),
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_task_status(self, task_id: str) -> dict:
        """Check video indexing status."""
        try:
            result = await self._request("GET", f"/tasks/{task_id}")
            return {
                "status": result.get("status"),
                "video_id": result.get("video_id"),
                "error": result.get("error"),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def search_interview_moments(
        self,
        video_id: str,
        query: str
    ) -> list:
        """
        Semantic search within interview video.
        Example queries: "explaining their approach", "debugging", "discussing tradeoffs"

        Note: TwelveLabs v1.3 searches at index level, not video level.
        We filter results client-side by video_id.
        """
        index_id = await self.get_or_create_index()
        if not index_id:
            return []

        try:
            # v1.3 API requires multipart/form-data format with separate search_options
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{TWELVELABS_API_URL}/search",
                    headers={"x-api-key": self.api_key},
                    files=[
                        ("index_id", (None, index_id)),
                        ("query_text", (None, query)),
                        ("search_options", (None, "visual")),
                        ("search_options", (None, "audio")),
                    ],
                )
                response.raise_for_status()
                result = response.json()

            # Filter results by video_id (v1.3 API doesn't support video-level filtering)
            clips = result.get("data", [])
            filtered_clips = [
                clip for clip in clips
                if clip.get("video_id") == video_id
            ]

            return [
                {
                    "start_time": clip.get("start"),
                    "end_time": clip.get("end"),
                    # v1.3 returns "score" (0-100) and "confidence" (high/medium/low)
                    "confidence": clip.get("score", 50) / 100.0,
                    "thumbnail_url": clip.get("thumbnail_url"),
                    "transcript": clip.get("transcription", ""),
                }
                for clip in filtered_clips
            ]
        except Exception as e:
            print(f"TwelveLabs search error: {e}")
            return []

    async def generate_interview_summary(self, video_id: str) -> str:
        """
        Generate a comprehensive summary of the interview.

        Note: TwelveLabs v1.3 removed the /summarize endpoint.
        We use search to find key moments and generate a summary based on that.
        """
        try:
            # Search for key interview moments to build context
            key_queries = [
                "explaining approach",
                "discussing solution",
                "problem solving",
            ]

            all_moments = []
            for query in key_queries:
                moments = await self.search_interview_moments(video_id, query)
                all_moments.extend(moments[:2])  # Top 2 per query

            if not all_moments:
                return "Interview video indexed successfully. Key moments can be searched using the search feature."

            # Build summary from found moments
            moment_count = len(all_moments)
            return f"Interview video analyzed. Found {moment_count} key moments including problem-solving discussions, approach explanations, and technical decision points. Use the search feature to explore specific topics."

        except Exception as e:
            print(f"TwelveLabs summary error: {e}")
            return ""

    async def generate_highlights(self, video_id: str) -> str:
        """Generate bullet-point highlights for quick recruiter review."""
        # TwelveLabs v1.3 removed the /generate endpoint
        # Highlights are now extracted via search in extract_highlight_clips
        return ""

    async def extract_highlight_clips(self, video_id: str) -> list:
        """
        Extract key moments for recruiter review using semantic search.
        Returns timestamped clips for each category.
        """
        highlight_queries = [
            ("approach", "candidate explaining their problem-solving approach"),
            ("debugging", "candidate debugging and fixing an error"),
            ("tradeoffs", "candidate discussing tradeoffs or alternative solutions"),
            ("questions", "candidate asking clarifying questions"),
            ("testing", "candidate discussing or writing tests"),
            ("optimization", "candidate optimizing or refactoring code"),
        ]

        highlights = []
        for category, query in highlight_queries:
            try:
                moments = await self.search_interview_moments(video_id, query)
                for moment in moments[:2]:  # Top 2 per category
                    highlights.append({
                        "category": category,
                        "query": query,
                        "start": moment["start_time"],
                        "end": moment["end_time"],
                        "confidence": moment["confidence"],
                        "transcript": moment.get("transcript", ""),
                    })
            except Exception as e:
                print(f"Error extracting {category} highlights: {e}")

        # Sort by confidence and return top highlights
        highlights.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return highlights[:10]

    async def analyze_communication_style(self, video_id: str) -> dict:
        """
        Analyze candidate's communication patterns using Gemini AI.

        Uses TwelveLabs search to extract transcript snippets,
        then sends to Gemini for detailed communication analysis.
        """
        try:
            # First, gather transcript snippets from various communication moments
            search_queries = [
                "explaining approach",
                "discussing solution",
                "asking questions",
                "technical explanation",
            ]

            all_transcripts = []
            for query in search_queries:
                moments = await self.search_interview_moments(video_id, query)
                for moment in moments[:3]:  # Top 3 per query
                    if moment.get("transcript"):
                        all_transcripts.append(moment["transcript"])

            if not all_transcripts:
                print("[TwelveLabs] No transcripts found for communication analysis")
                return {
                    "clarity": {"score": 3, "reason": "No transcript data available for analysis."},
                    "confidence": {"score": 3, "reason": "No transcript data available for analysis."},
                    "collaboration": {"score": 3, "reason": "No transcript data available for analysis."},
                    "technical_depth": {"score": 3, "reason": "No transcript data available for analysis."},
                }

            # Use Gemini (or fallback to GPT-4o) to analyze the transcripts
            from services.backboard import BackboardService
            backboard = BackboardService(user_id="system")

            transcript_text = "\n\n".join(all_transcripts[:10])  # Limit to avoid token overflow

            system_prompt = """You analyze interview communication skills. Return only valid JSON.
The JSON must have 4 keys: clarity, confidence, collaboration, technical_depth.
Each key has score (1-5) and reason (under 15 words).
Example format: the word clarity in quotes, colon, open brace, the word score in quotes, colon, number, etc.
No markdown code blocks."""

            user_message = f"""Analyze these interview transcript snippets and rate communication skills 1-5:

{transcript_text[:2000]}"""

            # Use GPT-4o via Backboard for reliable analysis
            # (Gemini free tier has strict rate limits)
            response = await backboard._call_model(
                assistant_name="CommunicationAnalysisAssistant",
                system_prompt=system_prompt,
                user_message=user_message,
                llm_provider="openai",
                model_name="gpt-4o",
                thread_key="communication_analysis",
            )

            # Parse the response
            try:
                # Strip markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith("```"):
                    clean_response = clean_response.split("\n", 1)[1] if "\n" in clean_response else clean_response[3:]
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()

                analysis = json.loads(clean_response)
                print(f"[TwelveLabs] Gemini communication analysis complete: {analysis}")
                return analysis
            except json.JSONDecodeError as e:
                print(f"[TwelveLabs] Failed to parse Gemini response: {e}")
                print(f"[TwelveLabs] Raw response: {response}")
                return {
                    "clarity": {"score": 3, "reason": "Analysis parsing failed."},
                    "confidence": {"score": 3, "reason": "Analysis parsing failed."},
                    "collaboration": {"score": 3, "reason": "Analysis parsing failed."},
                    "technical_depth": {"score": 3, "reason": "Analysis parsing failed."},
                }

        except Exception as e:
            print(f"TwelveLabs communication analysis error: {e}")
            return {}


    async def get_video_streaming_info(self, twelvelabs_video_id: str) -> dict:
        """
        Get streaming URLs and metadata from TwelveLabs for a video.

        Returns dict with stream_url, thumbnail_url, and duration.
        """
        index_id = await self.get_or_create_index()
        if not index_id or not self.api_key:
            return {}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{TWELVELABS_API_URL}/indexes/{index_id}/videos/{twelvelabs_video_id}",
                    headers={"x-api-key": self.api_key},
                )
                response.raise_for_status()
                data = response.json()

                result = {}

                # Extract HLS streaming info
                hls = data.get("hls", {})
                if hls.get("video_url"):
                    result["stream_url"] = hls["video_url"]
                if hls.get("thumbnail_urls") and len(hls["thumbnail_urls"]) > 0:
                    result["thumbnail_url"] = hls["thumbnail_urls"][0]

                # Extract duration from system metadata
                system_metadata = data.get("system_metadata", {})
                if system_metadata.get("duration"):
                    result["duration"] = system_metadata["duration"]

                print(f"[TwelveLabs] Got streaming info for {twelvelabs_video_id}: {list(result.keys())}")
                return result

        except Exception as e:
            print(f"[TwelveLabs] Error getting streaming info: {e}")
            return {}


# Standalone functions for background tasks (backward compatibility)


async def get_video_streaming_info(twelvelabs_video_id: str) -> dict:
    """Get streaming URLs for a video from TwelveLabs."""
    service = TwelveLabsService()
    return await service.get_video_streaming_info(twelvelabs_video_id)


async def get_or_create_index() -> Optional[str]:
    """Get or create a TwelveLabs index for the application."""
    service = TwelveLabsService()
    return await service.get_or_create_index()


async def upload_video_to_twelvelabs(
    video_id: str,
    user_id: str,
    file_path: str,
):
    """Upload and index a video in TwelveLabs."""
    settings = get_settings()

    print(f"[TwelveLabs] Processing video {video_id} for user {user_id}")

    if not settings.twelvelabs_api_key:
        # TwelveLabs not configured - mark as ready but no analysis
        print("[TwelveLabs] WARNING: TWELVELABS_API_KEY not configured!")
        print("[TwelveLabs] Video will be marked as ready but NO AI analysis will be performed.")
        print("[TwelveLabs] Set TWELVELABS_API_KEY environment variable to enable video analysis.")
        await Collections.videos().update_one(
            {"_id": video_id},
            {"$set": {
                "status": "ready",
                "summary": None,
                "highlights": [],
                "communication_analysis": None,
                "twelvelabs_not_configured": True,
            }},
        )
        return

    try:
        print(f"[TwelveLabs] API key configured, starting video indexing...")
        await Collections.videos().update_one(
            {"_id": video_id},
            {"$set": {"status": "indexing"}},
        )

        index_id = await get_or_create_index()
        if not index_id:
            print(f"[TwelveLabs] ERROR: Failed to get or create index")
            await Collections.videos().update_one(
                {"_id": video_id},
                {"$set": {"status": "failed"}},
            )
            return

        print(f"[TwelveLabs] Using index: {index_id}")
        headers = {"x-api-key": settings.twelvelabs_api_key}

        # Get content type from video document
        video_doc = await Collections.videos().find_one({"_id": video_id})
        content_type = video_doc.get("content_type", "video/mp4") if video_doc else "video/mp4"
        print(f"[TwelveLabs] Using content type: {content_type}")

        async with httpx.AsyncClient() as client:
            # Upload video - read file content into memory first for reliable async operation
            print(f"[TwelveLabs] Uploading video file: {file_path}")
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Debug: Log file size and first bytes to help diagnose issues
            file_size = len(file_content)
            print(f"[TwelveLabs] File size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
            print(f"[TwelveLabs] First 12 bytes (hex): {file_content[:12].hex()}")

            if file_size < 10000:  # Less than 10KB is suspicious
                print(f"[TwelveLabs] WARNING: File is very small, may not be a valid video")

            files = {"video_file": (os.path.basename(file_path), file_content, content_type)}
            data = {"index_id": index_id}

            response = await client.post(
                f"{TWELVELABS_API_URL}/tasks",
                headers=headers,
                files=files,
                data=data,
                timeout=300.0,
            )

            if response.status_code not in [200, 201]:
                print(f"[TwelveLabs] ERROR: Upload failed: {response.text}")
                await Collections.videos().update_one(
                    {"_id": video_id},
                    {"$set": {"status": "failed"}},
                )
                return

            result = response.json()
            task_id = result.get("_id")
            twelvelabs_video_id = result.get("video_id")
            print(f"[TwelveLabs] Upload successful! Task ID: {task_id}, Video ID: {twelvelabs_video_id}")

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

            # Poll for completion
            print(f"[TwelveLabs] Polling for indexing completion (max 5 minutes)...")
            service = TwelveLabsService()
            poll_count = 0
            for _ in range(60):  # Max 5 minutes
                await asyncio.sleep(5)
                poll_count += 1

                status = await service.get_task_status(task_id)
                print(f"[TwelveLabs] Poll #{poll_count}: status = {status['status']}")

                if status["status"] == "ready":
                    twelvelabs_video_id = status["video_id"]
                    print(f"[TwelveLabs] Video indexed! Starting AI analysis...")

                    # Run full analysis
                    print(f"[TwelveLabs] Running: generate_interview_summary, extract_highlight_clips, analyze_communication_style")
                    summary, highlights, communication = await asyncio.gather(
                        service.generate_interview_summary(twelvelabs_video_id),
                        service.extract_highlight_clips(twelvelabs_video_id),
                        service.analyze_communication_style(twelvelabs_video_id),
                    )

                    print(f"[TwelveLabs] Analysis complete!")
                    print(f"[TwelveLabs] Summary length: {len(summary) if summary else 0} chars")
                    print(f"[TwelveLabs] Highlights count: {len(highlights) if highlights else 0}")
                    print(f"[TwelveLabs] Communication analysis: {communication}")

                    await Collections.videos().update_one(
                        {"_id": video_id},
                        {
                            "$set": {
                                "status": "ready",
                                "twelvelabs_video_id": twelvelabs_video_id,
                                "summary": summary,
                                "highlights": highlights,
                                "communication_analysis": communication,
                                "ready_at": datetime.utcnow(),
                            }
                        },
                    )

                    # Update passport with video insights
                    await Collections.passports().update_one(
                        {"user_id": user_id},
                        {
                            "$set": {
                                "interview_video_id": video_id,
                                "interview_summary": summary,
                                "interview_highlights": highlights,
                                "communication_scores": communication,
                            }
                        },
                    )

                    # Clean up temp file
                    if os.path.exists(file_path):
                        os.remove(file_path)

                    print(f"[TwelveLabs] Video {video_id} processing complete!")
                    return

                elif status["status"] == "failed":
                    print(f"[TwelveLabs] ERROR: Indexing failed: {status.get('error')}")
                    await Collections.videos().update_one(
                        {"_id": video_id},
                        {"$set": {"status": "failed", "error": status.get("error")}},
                    )
                    return

            # Timeout
            print(f"[TwelveLabs] ERROR: Indexing timed out after 5 minutes")
            await Collections.videos().update_one(
                {"_id": video_id},
                {"$set": {"status": "failed", "error": "Indexing timeout"}},
            )

    except Exception as e:
        print(f"[TwelveLabs] ERROR: {e}")
        await Collections.videos().update_one(
            {"_id": video_id},
            {"$set": {"status": "failed", "error": str(e)}},
        )


async def search_video(twelvelabs_video_id: str, query: str) -> list[dict]:
    """Search a video for specific moments."""
    service = TwelveLabsService()
    return await service.search_interview_moments(twelvelabs_video_id, query)
