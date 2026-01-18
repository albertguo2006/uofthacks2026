#!/usr/bin/env python3
"""
Create a new TwelveLabs index with conversation model enabled for transcription.
This fixes the issue where videos don't have transcripts.
"""

import os
import sys
import asyncio
import httpx
from datetime import datetime

# Add the API directory to path to import the service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

TWELVELABS_API_KEY = os.environ.get("TWELVELABS_API_KEY", "tlk_1DQH50T1G3MK2B26Q3GE02SGDTFS")
TWELVELABS_API_URL = "https://api.twelvelabs.io/v1.3"

async def create_new_index():
    """Create a new TwelveLabs index with conversation model enabled."""

    headers = {
        "x-api-key": TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }

    # Create unique index name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    index_name = f"skillpulse-interviews-transcribed-{timestamp}"

    async with httpx.AsyncClient() as client:
        # First, list existing indexes to see what we have
        print("Listing existing indexes...")
        response = await client.get(
            f"{TWELVELABS_API_URL}/indexes",
            headers=headers,
            params={"page": 1, "page_size": 20}
        )

        if response.status_code == 200:
            indexes = response.json()
            print(f"Found {len(indexes.get('data', []))} existing indexes:")
            for idx in indexes.get('data', []):
                print(f"  - {idx.get('index_name')} (ID: {idx.get('_id')})")
                models = idx.get('models', [])
                if models:
                    options = models[0].get('model_options', [])
                    has_conversation = 'conversation' in options
                    print(f"    Model options: {options}")
                    print(f"    Has transcription: {'✅' if has_conversation else '❌'}")

        # Create new index with conversation model
        print(f"\nCreating new index: {index_name}")
        create_payload = {
            "index_name": index_name,
            "models": [
                {
                    "model_name": "marengo2.7",
                    "model_options": ["visual", "audio", "conversation"],
                }
            ],
        }

        response = await client.post(
            f"{TWELVELABS_API_URL}/indexes",
            headers=headers,
            json=create_payload,
            timeout=30.0,
        )

        if response.status_code in [200, 201]:
            index_data = response.json()
            index_id = index_data.get("_id")
            print(f"\n✅ Successfully created new index!")
            print(f"   Index Name: {index_name}")
            print(f"   Index ID: {index_id}")
            print(f"   Model: marengo2.7")
            print(f"   Options: visual, audio, conversation (transcription enabled)")

            print("\n📝 Next Steps:")
            print("1. Update your .env file:")
            print(f"   TWELVELABS_INDEX_ID={index_id}")
            print("\n2. Update apps/api/.env file:")
            print(f"   TWELVELABS_INDEX_ID={index_id}")
            print("\n3. Restart the API server for changes to take effect")
            print("\n4. New videos uploaded will now have transcriptions!")
            print("\nNote: Existing videos in the old index will NOT have transcriptions.")
            print("You would need to re-upload them to get transcripts.")

            return index_id
        else:
            print(f"❌ Failed to create index: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

if __name__ == "__main__":
    index_id = asyncio.run(create_new_index())
    if index_id:
        print(f"\n🎉 New index created successfully: {index_id}")
    else:
        print("\n❌ Failed to create new index")