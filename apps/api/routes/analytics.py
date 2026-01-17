from fastapi import APIRouter, Depends, HTTPException, Query, status

from middleware.auth import get_current_user
from services.amplitude import fetch_event_segmentation

router = APIRouter()


@router.get("/amplitude/segmentation")
async def get_amplitude_segmentation(
    event_type: str = Query(..., min_length=1),
    start: str = Query(..., min_length=8, max_length=8),
    end: str = Query(..., min_length=8, max_length=8),
    interval: int = Query(1, ge=1),
    metric: str = Query("totals", min_length=1),
    current_user: dict = Depends(get_current_user),
):
    """Fetch Amplitude event segmentation data for the given event."""
    _ = current_user

    try:
        return await fetch_event_segmentation(
            event_type=event_type,
            start=start,
            end=end,
            interval=interval,
            metric=metric,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch data from Amplitude",
        ) from exc
