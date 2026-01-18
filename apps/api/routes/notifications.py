from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional, Literal
from datetime import datetime
from bson import ObjectId
from models.notification import (
    Notification,
    NotificationCreate,
    NotificationUpdate,
    InterviewRequest,
    NotificationInDB
)
from models.user import User
from middleware.auth import get_current_user
from db.collections import Collections

router = APIRouter()


@router.get("/")
async def get_notifications(
    filter: Optional[Literal["all", "unread"]] = Query("all"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for the current user."""
    query = {"recipient_id": current_user["user_id"]}

    if filter == "unread":
        query["is_read"] = False

    cursor = Collections.db().notifications.find(query).sort("created_at", -1).skip(skip).limit(limit)
    notifications = []

    async for doc in cursor:
        doc["notification_id"] = str(doc["_id"])
        notifications.append(Notification(**doc))

    return {"notifications": notifications}


@router.get("/count", response_model=dict)
async def get_notification_count(
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """Get notification counts for the current user."""
    total_count = await Collections.db().notifications.count_documents({"recipient_id": current_user["user_id"]})
    unread_count = await Collections.db().notifications.count_documents({
        "recipient_id": current_user["user_id"],
        "is_read": False
    })

    return {
        "total": total_count,
        "unread": unread_count
    }


@router.get("/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: str,
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific notification."""
    try:
        doc = await Collections.db().notifications.find_one({
            "_id": ObjectId(notification_id),
            "recipient_id": current_user["user_id"]
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid notification ID")

    if not doc:
        raise HTTPException(status_code=404, detail="Notification not found")

    doc["notification_id"] = str(doc["_id"])
    return Notification(**doc)


@router.patch("/{notification_id}", response_model=Notification)
async def update_notification(
    notification_id: str,
    update: NotificationUpdate,
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """Update a notification (mark as read/unread)."""
    try:
        # Prepare update data
        update_data = {}
        if update.is_read is not None:
            update_data["is_read"] = update.is_read
            if update.is_read:
                update_data["read_at"] = datetime.utcnow()
            else:
                update_data["read_at"] = None

        # Update the notification
        result = await Collections.db().notifications.update_one(
            {
                "_id": ObjectId(notification_id),
                "recipient_id": current_user["user_id"]
            },
            {"$set": update_data}
        )
    except:
        raise HTTPException(status_code=400, detail="Invalid notification ID")

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Return updated notification
    doc = await Collections.db().notifications.find_one({"_id": ObjectId(notification_id)})
    doc["notification_id"] = str(doc["_id"])
    return Notification(**doc)


@router.post("/mark-all-read", response_model=dict)
async def mark_all_as_read(
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """Mark all notifications as read for the current user."""
    result = await Collections.db().notifications.update_many(
        {
            "recipient_id": current_user["user_id"],
            "is_read": False
        },
        {
            "$set": {
                "is_read": True,
                "read_at": datetime.utcnow()
            }
        }
    )

    return {
        "modified_count": result.modified_count,
        "message": f"Marked {result.modified_count} notifications as read"
    }


@router.post("/interview-request", response_model=Notification)
async def send_interview_request(
    interview_request: InterviewRequest,
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """Send an interview request to a candidate (recruiter only)."""
    if current_user.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can send interview requests")

    # Verify candidate exists
    # Try multiple approaches to find the candidate since MongoDB ID formats may vary
    candidate = None

    # First try as string _id (most common case)
    candidate = await Collections.users().find_one({"_id": interview_request.candidate_id})

    # If not found and looks like an ObjectId hex string, try converting to ObjectId
    if not candidate and len(interview_request.candidate_id) == 24:
        try:
            candidate = await Collections.users().find_one({"_id": ObjectId(interview_request.candidate_id)})
        except:
            pass

    # If still not found, try searching by user_id field (in case it's stored separately)
    if not candidate:
        candidate = await Collections.users().find_one({"user_id": interview_request.candidate_id})

    if not candidate:
        # Log available candidates for debugging
        sample_candidates = await Collections.users().find({"role": "candidate"}).limit(3).to_list(3)
        print(f"DEBUG: Available candidate IDs: {[str(c.get('_id')) for c in sample_candidates]}")
        raise HTTPException(
            status_code=404,
            detail=f"Candidate not found. Please refresh the candidates list and try again."
        )

    # Get recruiter's company info (if available)
    recruiter = await Collections.users().find_one({"_id": current_user["user_id"]})

    # Create notification - ensure recipient_id is stored as string to match auth.py format
    candidate_id_str = str(candidate.get("_id", interview_request.candidate_id))
    notification_data = {
        "recipient_id": candidate_id_str,
        "sender_id": current_user["user_id"],
        "type": "interview_request",
        "title": f"Interview Request from {interview_request.company_name}",
        "message": interview_request.message or f"You have been invited for an interview with {interview_request.company_name}",
        "is_read": False,
        "created_at": datetime.utcnow(),
        "metadata": {
            "job_id": interview_request.job_id,
            "job_title": interview_request.job_title,
            "company_name": interview_request.company_name,
            "interview_date": interview_request.interview_date.isoformat() if interview_request.interview_date else None,
            "interview_type": interview_request.interview_type,
            "meeting_link": interview_request.meeting_link,
            "recruiter_name": recruiter.get("display_name", "Recruiter"),
            "recruiter_email": recruiter.get("email")
        }
    }

    result = await Collections.db().notifications.insert_one(notification_data)
    notification_data["notification_id"] = str(result.inserted_id)
    notification_data["_id"] = str(result.inserted_id)

    return Notification(**notification_data)


@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: str,
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification."""
    try:
        result = await Collections.db().notifications.delete_one({
            "_id": ObjectId(notification_id),
            "recipient_id": current_user["user_id"]
        })
    except:
        raise HTTPException(status_code=400, detail="Invalid notification ID")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification deleted successfully"}