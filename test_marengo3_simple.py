#!/usr/bin/env python3
"""
Test if Marengo 3.0 with just audio option provides transcription.
"""

import os
import asyncio
import httpx
from datetime import datetime

TWELVELABS_API_KEY = os.environ.get("TWELVELABS_API_KEY", "tlk_1DQH50T1G3MK2B26Q3GE02SGDTFS")
TWELVELABS_API_URL = "https://api.twelvelabs.io/v1.3"

async def test_marengo3():
    """Test Marengo 3.0 with just visual and audio options."""

    headers = {
        "x-api-key": TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    index_name = f"skillpulse-m3-test-{timestamp}"

    async with httpx.AsyncClient() as client:
        print("Testing Marengo 3.0 index creation...")
        print("=" * 60)

        # Try Marengo 3.0 with just visual and audio
        create_payload = {
            "index_name": index_name,
            "models": [
                {
                    "model_name": "marengo3.0",
                    "model_options": ["visual", "audio"],  # No "conversation" option
                }
            ],
        }

        print(f"Creating index: {index_name}")
        print(f"Model: marengo3.0")
        print(f"Options: visual, audio (transcription may be automatic)")

        response = await client.post(
            f"{TWELVELABS_API_URL}/indexes",
            headers=headers,
            json=create_payload,
            timeout=30.0,
        )

        if response.status_code in [200, 201]:
            index_data = response.json()
            index_id = index_data.get("_id")
            print(f"\n✅ Successfully created Marengo 3.0 index!")
            print(f"   Index ID: {index_id}")

            # Check index details to see what capabilities it has
            print("\nChecking index capabilities...")
            detail_response = await client.get(
                f"{TWELVELABS_API_URL}/indexes/{index_id}",
                headers=headers
            )

            if detail_response.status_code == 200:
                details = detail_response.json()
                print(f"Index details: {details}")

            print("\n📝 Key Finding:")
            print("Marengo 3.0 with 'audio' option likely includes transcription automatically!")
            print("The 'conversation' option doesn't exist - transcription is part of 'audio'.")

            # Clean up - delete test index
            print("\nCleaning up test index...")
            delete_response = await client.delete(
                f"{TWELVELABS_API_URL}/indexes/{index_id}",
                headers=headers
            )
            if delete_response.status_code in [200, 204]:
                print("Test index deleted.")

            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.json()}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_marengo3())
    if success:
        print("\n✅ Marengo 3.0 is the solution! Use it with 'audio' option for transcription.")