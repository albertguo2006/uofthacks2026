#!/usr/bin/env python3
"""
Create the production TwelveLabs index with Marengo 3.0 for transcription support.
"""

import os
import asyncio
import httpx
from datetime import datetime

TWELVELABS_API_KEY = os.environ.get("TWELVELABS_API_KEY", "tlk_1DQH50T1G3MK2B26Q3GE02SGDTFS")
TWELVELABS_API_URL = "https://api.twelvelabs.io/v1.3"

async def create_production_index():
    """Create production TwelveLabs index with Marengo 3.0."""

    headers = {
        "x-api-key": TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }

    # Production index name
    index_name = "skillpulse-interviews-production"

    async with httpx.AsyncClient() as client:
        print("Creating Production TwelveLabs Index with Transcription Support")
        print("=" * 60)

        # Create production index with Marengo 3.0
        create_payload = {
            "index_name": index_name,
            "models": [
                {
                    "model_name": "marengo3.0",
                    "model_options": ["visual", "audio"],  # Audio includes transcription in Marengo 3.0
                }
            ],
        }

        print(f"Index Name: {index_name}")
        print(f"Model: Marengo 3.0")
        print(f"Capabilities:")
        print("  • Visual understanding")
        print("  • Audio understanding")
        print("  • Speech-to-text transcription (automatic with Marengo 3.0)")
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

            print(f"\n✅ SUCCESS! Production index created with full transcription support!")
            print(f"\n   Index ID: {index_id}")
            print(f"   Index Name: {index_name}")
            print(f"   Model: Marengo 3.0")
            print(f"   Expires: {index_data.get('expires_at', 'N/A')}")

            print("\n" + "=" * 60)
            print("📝 REQUIRED CONFIGURATION UPDATES:")
            print("=" * 60)

            print("\n1. Update apps/api/.env file:")
            print(f"\n   TWELVELABS_INDEX_ID={index_id}")

            print("\n2. Verify the code update in apps/api/services/twelvelabs.py:")
            print('   Line 100 should be: "model_name": "marengo3.0"')

            print("\n3. Restart the API server to use the new index:")
            print("   Find the uvicorn process: ps aux | grep uvicorn")
            print("   Kill it and restart")

            print("\n" + "=" * 60)
            print("🎯 WHAT THIS FIXES:")
            print("=" * 60)
            print("✅ Videos will now have full speech-to-text transcription")
            print("✅ Interview analysis will include what candidates said")
            print("✅ Communication analysis will work properly")
            print("✅ Semantic search within videos will find spoken content")

            print("\n⚠️  IMPORTANT NOTES:")
            print("-" * 60)
            print("• Old videos in the previous index will NOT have transcripts")
            print("• Only NEW videos uploaded after this change will have transcription")
            print("• To get transcripts for old videos, they must be re-uploaded")
            print("• The old index (696c1b71cafce60cf069e741) can be deleted later")

            return index_id
        else:
            print(f"\n❌ Failed to create index: {response.status_code}")
            error_data = response.json()
            print(f"   Error: {error_data}")
            return None

if __name__ == "__main__":
    index_id = asyncio.run(create_production_index())
    if index_id:
        print(f"\n🚀 Next step: Update TWELVELABS_INDEX_ID in .env to: {index_id}")
    else:
        print("\n❌ Index creation failed. Check your API key and try again.")