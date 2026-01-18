#!/usr/bin/env python3
"""
Check available TwelveLabs models and their capabilities.
"""

import os
import sys
import asyncio
import httpx

TWELVELABS_API_KEY = os.environ.get("TWELVELABS_API_KEY", "tlk_1DQH50T1G3MK2B26Q3GE02SGDTFS")
TWELVELABS_API_URL = "https://api.twelvelabs.io/v1.3"

async def check_models():
    """Check available models and their options."""

    headers = {
        "x-api-key": TWELVELABS_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        # Get models information
        print("Checking TwelveLabs models and their capabilities...")
        print("=" * 60)

        # Try to get model information from the engines endpoint
        try:
            response = await client.get(
                f"{TWELVELABS_API_URL}/engines",
                headers=headers
            )

            if response.status_code == 200:
                engines = response.json()
                print("Available engines:")
                print(engines)
            else:
                print(f"Engines endpoint returned: {response.status_code}")
        except Exception as e:
            print(f"Engines endpoint not available: {e}")

        # Check different model configurations
        models_to_test = [
            # Marengo models
            ("marengo2.7", ["visual", "audio"]),
            ("marengo2.7", ["visual", "audio", "conversation"]),
            ("marengo2.6", ["visual", "audio", "conversation"]),
            ("marengo2.5", ["visual", "audio", "conversation"]),
            # Pegasus models (older, might support conversation)
            ("pegasus1.1", ["visual", "audio", "conversation"]),
            ("pegasus1", ["visual", "audio", "conversation"]),
            # Marengo 3 (newest)
            ("marengo3", ["visual", "audio", "conversation"]),
            ("marengo-3.0", ["visual", "audio", "conversation"]),
        ]

        print("\nTesting model configurations:")
        print("-" * 60)

        for model_name, options in models_to_test:
            print(f"\nTesting: {model_name} with options {options}")

            # Try to validate by creating a temporary index
            create_payload = {
                "index_name": f"test-index-{model_name.replace('.', '-')}",
                "models": [
                    {
                        "model_name": model_name,
                        "model_options": options,
                    }
                ],
            }

            try:
                # Use a dry run or validation endpoint if available
                response = await client.post(
                    f"{TWELVELABS_API_URL}/indexes",
                    headers=headers,
                    json=create_payload,
                    timeout=10.0,
                )

                if response.status_code in [200, 201]:
                    print(f"  ✅ Valid configuration!")
                    # Delete the test index
                    index_id = response.json().get("_id")
                    if index_id:
                        await client.delete(
                            f"{TWELVELABS_API_URL}/indexes/{index_id}",
                            headers=headers
                        )
                        print(f"  (Test index deleted)")
                else:
                    error_data = response.json()
                    error_msg = error_data.get("message", "Unknown error")
                    if "invalid options" in error_msg.lower():
                        print(f"  ❌ Invalid options for this model")
                    elif "model" in error_msg.lower() and "not" in error_msg.lower():
                        print(f"  ❌ Model not available")
                    else:
                        print(f"  ❌ {error_msg}")
            except Exception as e:
                print(f"  ❌ Error: {e}")

        print("\n" + "=" * 60)
        print("Based on TwelveLabs documentation:")
        print("- Marengo 2.7: Visual and audio understanding only")
        print("- Marengo 3.0: Includes conversation/transcription support")
        print("- For transcription, you need Marengo 3.0 or later")
        print("\nRecommendation: Use Marengo 3.0 with 'conversation' option")

if __name__ == "__main__":
    asyncio.run(check_models())