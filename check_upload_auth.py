#!/usr/bin/env python3
"""
Check the authentication and upload flow for proctored videos.
"""

import os
import asyncio
import httpx
from datetime import datetime

API_URL = "http://localhost:8000"

async def check_upload_auth():
    """Check the video upload authentication flow."""

    async with httpx.AsyncClient() as client:
        print("Checking Video Upload Authentication")
        print("=" * 60)

        # Step 1: Check if we're in dev mode
        print("\n1. Testing Dev Mode Access (no auth required):")
        print("-" * 40)

        headers_dev = {
            "X-Dev-Mode": "true",
            "X-Dev-Role": "candidate"
        }

        try:
            response = await client.get(
                f"{API_URL}/auth/me",
                headers=headers_dev,
                timeout=5.0
            )

            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Dev mode working")
                print(f"   User ID: {user_data.get('user_id')}")
                print(f"   Role: {user_data.get('role')}")
            else:
                print(f"❌ Dev mode failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Step 2: Check proctoring endpoints
        print("\n2. Testing Proctoring Endpoints:")
        print("-" * 40)

        # Try to start a proctoring session
        try:
            response = await client.post(
                f"{API_URL}/proctoring/start",
                headers=headers_dev,
                json={
                    "task_id": "test-task-123",
                    "camera_enabled": False
                },
                timeout=5.0
            )

            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get("session_id")
                print(f"✅ Can start proctoring sessions")
                print(f"   Session ID: {session_id}")

                # Now test if we can access the upload endpoint (without actually uploading)
                print("\n3. Testing Upload Endpoint Access:")
                print("-" * 40)

                # Create minimal form data to test authentication
                form_data = {
                    "session_id": session_id,
                    "task_id": "test-task-123",
                    "is_proctored": "true"
                }

                # We'll send a OPTIONS request first to check CORS
                try:
                    response = await client.options(
                        f"{API_URL}/proctoring/upload-video",
                        headers={"Origin": "http://localhost:3000"},
                        timeout=5.0
                    )

                    if response.status_code in [200, 204]:
                        print("✅ CORS configured correctly")
                    else:
                        print(f"⚠️  CORS might be an issue: {response.status_code}")
                except:
                    print("⚠️  Could not check CORS")

                # The actual upload would happen here
                print("\n   Note: Actual file upload requires a video file")
                print("   The endpoint expects: video (file), session_id, task_id, is_proctored")

            else:
                print(f"❌ Cannot start proctoring: {response.status_code}")
                print(f"   Response: {response.text}")

        except Exception as e:
            print(f"❌ Error testing proctoring: {e}")

        # Step 3: Check TwelveLabs service status
        print("\n4. Checking TwelveLabs Service in API:")
        print("-" * 40)

        # This would be an internal check - the API should be using the new settings
        print("   The API server must be restarted after .env changes!")
        print("   Settings are cached with @lru_cache")

        # Check if videos collection has any recent failures
        print("\n5. Common Upload Failure Reasons:")
        print("-" * 40)
        print("   • API server not restarted after .env change")
        print("   • TwelveLabs index ID mismatch")
        print("   • File too large (check file size limits)")
        print("   • Browser not sending auth token properly")
        print("   • CORS blocking the request")

        print("\n" + "=" * 60)
        print("RECOMMENDATIONS:")
        print("=" * 60)

        print("\n1. Restart the API server to clear cached settings:")
        print("   ps aux | grep uvicorn")
        print("   kill <PID>")
        print("   cd apps/api && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")

        print("\n2. Check browser console for actual error:")
        print("   Open Developer Tools → Console")
        print("   Look for 'Failed to upload video:' message")

        print("\n3. Check API logs when upload is attempted:")
        print("   Look for '[DEBUG] Received video upload' messages")
        print("   Check for TwelveLabs error messages")

        print("\n4. Verify in MongoDB:")
        print("   db.videos.find({ status: 'failed' }).sort({ uploaded_at: -1 }).limit(1)")
        print("   Check the 'error' field for details")

if __name__ == "__main__":
    asyncio.run(check_upload_auth())