import httpx
from config import get_settings
from db.collections import Collections


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

            await Collections.events().update_one(
                {"_id": event_id},
                {"$set": {"forwarded_to_amplitude": success}},
            )

    except Exception as e:
        print(f"Failed to forward event to Amplitude: {e}")
        await Collections.events().update_one(
            {"_id": event_id},
            {"$set": {"forwarded_to_amplitude": False}},
        )


async def update_amplitude_user_properties(user_id: str, properties: dict):
    """Update user properties in Amplitude."""
    settings = get_settings()

    if not settings.amplitude_api_key:
        return

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
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
    except Exception as e:
        print(f"Failed to update Amplitude user properties: {e}")
