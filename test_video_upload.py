#!/usr/bin/env python3
"""
Test the video upload flow and identify where it's failing.
"""

import os
import asyncio
import httpx
from datetime import datetime

# Read from the .env file
TWELVELABS_API_KEY = "tlk_2CDMSHQ26H6HHZ2ZTDAD721EBDWY"
TWELVELABS_INDEX_ID = "696cbdc15859cae89da0e6a6"
TWELVELABS_API_URL = "https://api.twelvelabs.io/v1.3"

async def test_upload_flow():
    """Test each step of the video upload flow."""

    headers = {
        "x-api-key": TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        print("Testing TwelveLabs Video Upload Flow")
        print("=" * 60)

        # Step 1: Verify API key is valid
        print("\n1. Testing API Key validity:")
        print("-" * 40)
        try:
            response = await client.get(
                f"{TWELVELABS_API_URL}/indexes",
                headers=headers,
                timeout=30.0
            )

            if response.status_code == 200:
                print("✅ API Key is valid")
            else:
                print(f"❌ API Key invalid: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        except Exception as e:
            print(f"❌ Error testing API key: {e}")
            return

        # Step 2: Verify index exists and is accessible
        print("\n2. Testing Index access:")
        print("-" * 40)
        print(f"   Index ID: {TWELVELABS_INDEX_ID}")

        try:
            response = await client.get(
                f"{TWELVELABS_API_URL}/indexes/{TWELVELABS_INDEX_ID}",
                headers=headers,
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Index accessible")
                print(f"   Name: {data.get('index_name')}")
                print(f"   Videos: {data.get('video_count', 0)}")
                models = data.get('models', [])
                if models:
                    print(f"   Model: {models[0].get('model_name')}")
            elif response.status_code == 404:
                print(f"❌ Index not found")
                print("   The index ID doesn't exist for this API key")
                return
            elif response.status_code == 403:
                print(f"❌ Index access forbidden")
                print("   The API key doesn't have permission for this index")
                return
            else:
                print(f"❌ Index access failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        except Exception as e:
            print(f"❌ Error accessing index: {e}")
            return

        # Step 3: Test creating a video upload task
        print("\n3. Testing video upload task creation:")
        print("-" * 40)

        # Create a minimal test video upload task
        upload_payload = {
            "index_id": TWELVELABS_INDEX_ID,
            "video_url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",  # Test URL
            "video_title": "Test Upload " + datetime.now().strftime("%Y%m%d_%H%M%S"),
        }

        try:
            response = await client.post(
                f"{TWELVELABS_API_URL}/tasks",
                headers=headers,
                json=upload_payload,
                timeout=30.0
            )

            if response.status_code in [200, 201]:
                data = response.json()
                task_id = data.get("_id")
                print(f"✅ Can create upload tasks")
                print(f"   Task ID: {task_id}")

                # Delete/cancel the test task if possible
                # (TwelveLabs might not allow deletion, that's okay)

            else:
                print(f"❌ Cannot create upload tasks: {response.status_code}")
                print(f"   Response: {response.text}")

                # Parse the error
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        print(f"\n   Error Message: {error_data['message']}")
                    if "code" in error_data:
                        print(f"   Error Code: {error_data['code']}")
                except:
                    pass

        except Exception as e:
            print(f"❌ Error creating upload task: {e}")

        # Step 4: Check current settings in the API
        print("\n4. Checking API server configuration:")
        print("-" * 40)

        # Try to call the API's internal check endpoint
        try:
            api_response = await client.get(
                "http://localhost:8000/health",  # Or any endpoint to check if API is running
                timeout=5.0
            )

            if api_response.status_code == 200:
                print("✅ API server is running")
            else:
                print(f"⚠️  API server returned: {api_response.status_code}")
        except:
            print("❌ Cannot connect to API server at localhost:8000")

        print("\n" + "=" * 60)
        print("DIAGNOSTICS SUMMARY:")
        print("=" * 60)

        print("\nPossible issues:")
        print("1. If API key is invalid -> Check the key in .env")
        print("2. If index not found -> The index ID is wrong")
        print("3. If cannot create tasks -> Permissions or quota issue")
        print("4. If API server not running -> Restart the server")

        print("\nTo fix:")
        print("1. Make sure the API server restarted after .env changes")
        print("   Kill the uvicorn process and restart it")
        print("2. Check if the index ID is correct for this API key")
        print("3. Verify the API key has proper permissions")

async def check_api_restart():
    """Check if the API is using the new settings."""

    print("\n" + "=" * 60)
    print("CHECKING API SETTINGS CACHE:")
    print("=" * 60)

    print("\nThe API uses @lru_cache which caches settings!")
    print("You MUST restart the API server after changing .env")

    print("\nTo restart:")
    print("1. Find the process: ps aux | grep uvicorn")
    print("2. Kill it: kill <PID>")
    print("3. Restart: cd apps/api && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")

if __name__ == "__main__":
    asyncio.run(test_upload_flow())
    asyncio.run(check_api_restart())