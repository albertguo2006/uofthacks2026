#!/usr/bin/env python3
"""
Check what indexes are available with the new TwelveLabs API key.
"""

import os
import asyncio
import httpx

# Using the NEW API key from .env
TWELVELABS_API_KEY = "tlk_2CDMSHQ26H6HHZ2ZTDAD721EBDWY"
TWELVELABS_API_URL = "https://api.twelvelabs.io/v1.3"

async def check_new_key_access():
    """Check what the new API key has access to."""

    headers = {
        "x-api-key": TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        print("Checking new TwelveLabs API key...")
        print(f"API Key: {TWELVELABS_API_KEY[:10]}...")
        print("=" * 60)

        # 1. Check if we can list indexes
        print("\n1. Listing available indexes with new key:")
        print("-" * 40)
        try:
            response = await client.get(
                f"{TWELVELABS_API_URL}/indexes",
                headers=headers,
                params={"page": 1, "page_size": 20},
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                indexes = data.get('data', [])

                if indexes:
                    print(f"✅ Found {len(indexes)} index(es):")
                    for idx in indexes:
                        print(f"\n   Index Name: {idx.get('index_name')}")
                        print(f"   Index ID: {idx.get('_id')}")
                        print(f"   Video Count: {idx.get('video_count', 0)}")
                        models = idx.get('models', [])
                        if models:
                            print(f"   Model: {models[0].get('model_name')}")
                            print(f"   Options: {models[0].get('model_options')}")
                else:
                    print("❌ No indexes found with this API key")
                    print("   Need to create a new index")
            else:
                print(f"❌ Failed to list indexes: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error listing indexes: {e}")

        # 2. Try to access the old index ID
        print("\n2. Checking access to old index ID:")
        print("-" * 40)
        old_index_id = "696cba80cafce60cf069fe56"
        print(f"   Old Index ID: {old_index_id}")

        try:
            response = await client.get(
                f"{TWELVELABS_API_URL}/indexes/{old_index_id}",
                headers=headers,
                timeout=30.0
            )

            if response.status_code == 200:
                print("✅ Can access old index (unexpected!)")
            elif response.status_code == 404:
                print("❌ Cannot access old index - Not found")
                print("   This is expected - indexes are API key specific")
            elif response.status_code == 403:
                print("❌ Cannot access old index - Forbidden")
                print("   This is expected - indexes are API key specific")
            else:
                print(f"❌ Cannot access old index: {response.status_code}")
        except Exception as e:
            print(f"❌ Error checking old index: {e}")

        # 3. Check if we can create a new index
        print("\n3. Testing index creation capability:")
        print("-" * 40)
        try:
            # Try a dry run (will delete immediately if successful)
            test_payload = {
                "index_name": "test-api-key-validation",
                "models": [
                    {
                        "model_name": "marengo3.0",
                        "model_options": ["visual", "audio"],
                    }
                ],
            }

            response = await client.post(
                f"{TWELVELABS_API_URL}/indexes",
                headers=headers,
                json=test_payload,
                timeout=30.0
            )

            if response.status_code in [200, 201]:
                print("✅ Can create indexes with this API key")
                # Delete the test index
                test_id = response.json().get("_id")
                if test_id:
                    await client.delete(
                        f"{TWELVELABS_API_URL}/indexes/{test_id}",
                        headers=headers
                    )
                    print("   (Test index deleted)")
            else:
                print(f"❌ Cannot create indexes: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error testing index creation: {e}")

        print("\n" + "=" * 60)
        print("SOLUTION:")
        print("=" * 60)
        print("\n1. Clear the old index ID from .env:")
        print("   Remove or comment out: TWELVELABS_INDEX_ID=696cba80cafce60cf069fe56")
        print("\n2. Restart the API server to clear cached settings")
        print("\n3. The service will automatically create a new index with the new API key")
        print("\n4. Or manually create a new index and update TWELVELABS_INDEX_ID")

if __name__ == "__main__":
    asyncio.run(check_new_key_access())