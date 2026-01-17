import httpx
import json
from config import get_settings
from db.collections import Collections

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


async def forward_to_amplitude(
    event_id: str,
    user_id: str,
    event_type: str,
    timestamp: int,
    properties: dict,
    user_properties: dict = None,
):
    """Forward an event to Amplitude analytics."""
    settings = get_settings()

    if not settings.amplitude_api_key:
        # Amplitude not configured, mark as forwarded anyway
        print(f"{YELLOW}[Amplitude] Skipped '{event_type}' - API key not configured{RESET}")
        await Collections.events().update_one(
            {"_id": event_id},
            {"$set": {"forwarded_to_amplitude": True}},
        )
        return

    amplitude_event = {
        "user_id": user_id,
        "event_type": event_type,
        "time": timestamp,
        "event_properties": properties,
    }

    if user_properties:
        amplitude_event["user_properties"] = {"$set": user_properties}

    print(f"{BLUE}[Amplitude] Sending '{event_type}' for user {user_id[:8]}...{RESET}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api2.amplitude.com/2/httpapi",
                json={
                    "api_key": settings.amplitude_api_key,
                    "events": [amplitude_event],
                },
                timeout=10.0,
            )

            success = response.status_code == 200

            if success:
                print(f"{GREEN}[Amplitude] ✓ Sent '{event_type}' successfully{RESET}")
            else:
                print(f"{RED}[Amplitude] ✗ Failed '{event_type}' - HTTP {response.status_code}: {response.text[:100]}{RESET}")

            await Collections.events().update_one(
                {"_id": event_id},
                {"$set": {"forwarded_to_amplitude": success}},
            )

    except Exception as e:
        print(f"{RED}[Amplitude] ✗ Error sending '{event_type}': {e}{RESET}")
        await Collections.events().update_one(
            {"_id": event_id},
            {"$set": {"forwarded_to_amplitude": False}},
        )


async def update_amplitude_user_properties(user_id: str, properties: dict):
    """Update user properties in Amplitude."""
    settings = get_settings()

    if not settings.amplitude_api_key:
        print(f"{YELLOW}[Amplitude] Skipped user properties update - API key not configured{RESET}")
        return

    print(f"{BLUE}[Amplitude] Updating user properties for {user_id[:8]}...{RESET}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api2.amplitude.com/2/httpapi",
                json={
                    "api_key": settings.amplitude_api_key,
                    "events": [
                        {
                            "user_id": user_id,
                            "event_type": "$identify",
                            "user_properties": {"$set": properties},
                        }
                    ],
                },
                timeout=10.0,
            )
            if response.status_code == 200:
                print(f"{GREEN}[Amplitude] ✓ Updated user properties{RESET}")
            else:
                print(f"{RED}[Amplitude] ✗ Failed to update user properties - HTTP {response.status_code}{RESET}")
    except Exception as e:
        print(f"{RED}[Amplitude] ✗ Error updating user properties: {e}{RESET}")


async def fetch_event_segmentation(
    event_type: str,
    start: str,
    end: str,
    interval: int = 1,
    metric: str = "totals",
) -> dict:
    """Fetch event segmentation data from Amplitude Data API."""
    settings = get_settings()

    if not settings.amplitude_api_key or not settings.amplitude_secret_key:
        raise ValueError("Amplitude API key or secret key not configured")

    params = {
        "e": json.dumps({"event_type": event_type}),
        "start": start,
        "end": end,
        "i": interval,
        "m": metric,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://amplitude.com/api/2/events/segmentation",
            params=params,
            auth=(settings.amplitude_api_key, settings.amplitude_secret_key),
            timeout=20.0,
        )
        response.raise_for_status()
        return response.json()
