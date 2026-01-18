#!/usr/bin/env python3
"""
Create a new TwelveLabs index with Marengo 3.0 model for transcription support.
"""

import os
import sys
import asyncio
import httpx
from datetime import datetime

TWELVELABS_API_KEY = os.environ.get("TWELVELABS_API_KEY", "tlk_1DQH50T1G3MK2B26Q3GE02SGDTFS")
TWELVELABS_API_URL = "https://api.twelvelabs.io/v1.3"

async def create_marengo3_index():
    """Create a new TwelveLabs index with Marengo 3.0 for transcription."""

    headers = {
        "x-api-key": TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }

    # Create unique index name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    index_name = f"skillpulse-marengo3-{timestamp}"

    async with httpx.AsyncClient() as client:
        print("Creating new index with Marengo 3.0 for transcription support...")
        print("=" * 60)

        # Create new index with Marengo 3.0
        create_payload = {
            "index_name": index_name,
            "models": [
                {
                    "model_name": "marengo3.0",  # Using Marengo 3.0 for transcription
                    "model_options": ["visual", "audio", "conversation"],  # conversation enables transcription
                }
            ],
        }

        print(f"Index Name: {index_name}")
        print(f"Model: marengo3.0")
        print(f"Options: visual, audio, conversation")
        print("-" * 60)

        response = await client.post(
            f"{TWELVELABS_API_URL}/indexes",
            headers=headers,
            json=create_payload,
            timeout=30.0,
        )

        if response.status_code in [200, 201]:
            index_data = response.json()
            index_id = index_data.get("_id")
            print(f"\n✅ Successfully created new index with transcription support!")
            print(f"   Index ID: {index_id}")
            print(f"   Index Name: {index_name}")
            print(f"   Model: marengo3.0")
            print(f"   Capabilities:")
            print(f"     • Visual understanding ✅")
            print(f"     • Audio understanding ✅")
            print(f"     • Speech transcription ✅")

            print("\n📝 IMPORTANT - Update your configuration:")
            print("=" * 60)
            print("\n1. Update apps/api/.env file:")
            print(f"   TWELVELABS_INDEX_ID={index_id}")

            print("\n2. Also update the code in apps/api/services/twelvelabs.py (line 100-101):")
            print('   Change from: "model_name": "marengo2.7"')
            print('   Change to:   "model_name": "marengo3.0"')

            print("\n3. Restart the API server:")
            print("   Kill the current uvicorn process and restart it")

            print("\n4. Future videos will now have transcriptions!")

            print("\n⚠️  Note about existing videos:")
            print("   - Videos in the old index will NOT have transcriptions")
            print("   - You need to re-upload proctored session videos to get transcripts")
            print("   - The old index can be deleted from TwelveLabs dashboard if not needed")

            return index_id
        else:
            print(f"❌ Failed to create index: {response.status_code}")
            error_data = response.json()
            print(f"   Error: {error_data.get('message', 'Unknown error')}")
            if 'code' in error_data:
                print(f"   Code: {error_data.get('code')}")
            return None

if __name__ == "__main__":
    index_id = asyncio.run(create_marengo3_index())
    if index_id:
        print(f"\n🎉 Successfully created Marengo 3.0 index: {index_id}")
        print("   Videos uploaded to this index will have full transcription support!")
    else:
        print("\n❌ Failed to create new index")