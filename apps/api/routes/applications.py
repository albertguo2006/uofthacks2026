from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import uuid

from middleware.auth import get_current_user
from db.collections import Collections
from models.application import ApplicationCreate, Application, ApplicantInfo
from services.skillgraph import compute_job_fit

router = APIRouter()

ARCHETYPE_LABELS = {
    "fast_iterator": "Fast Iterator",
    "careful_tester": "Careful Tester",
    "debugger": "Debugger",
    "craftsman": "Code Craftsman",
}


@router.post("", response_model=Application)
async def apply_to_job(
    application_data: ApplicationCreate,
    current_user: dict = Depends(get_current_user),
):
    """Apply to a job posting (candidates only)."""
    if current_user.get("role") != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can apply to jobs",
        )

    # Check if job exists
    job = await Collections.jobs().find_one({"job_id": application_data.job_id})
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check if already applied
    existing = await Collections.applications().find_one({
        "job_id": application_data.job_id,
        "user_id": current_user["user_id"],
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already applied to this job",
        )

    application_id = f"app-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()

    application_doc = {
        "application_id": application_id,
        "job_id": application_data.job_id,
        "user_id": current_user["user_id"],
        "applied_at": now,
        "status": "pending",
    }

    await Collections.applications().insert_one(application_doc)

    return Application(
        application_id=application_id,
        job_id=application_data.job_id,
        user_id=current_user["user_id"],
        applied_at=now,
        status="pending",
    )


@router.get("/my", response_model=list[str])
async def get_my_applications(
    current_user: dict = Depends(get_current_user),
):
    """Get list of job IDs the current user has applied to."""
    cursor = Collections.applications().find({"user_id": current_user["user_id"]})
    job_ids = []
    async for app in cursor:
        job_ids.append(app["job_id"])
    return job_ids


@router.get("/job/{job_id}", response_model=list[ApplicantInfo])
async def get_job_applicants(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get all applicants for a job (recruiter who owns the job only)."""
    if current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can view applicants",
        )

    # Check if job exists and belongs to this recruiter
    job = await Collections.jobs().find_one({"job_id": job_id})
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.get("recruiter_id") != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view applicants for your own jobs",
        )

    # Get all applications for this job
    cursor = Collections.applications().find({"job_id": job_id})
    applicants = []

    async for application in cursor:
        user_id = application["user_id"]

        # Get user info
        user = await Collections.users().find_one({"_id": user_id})
        if not user:
            continue

        # Get passport for metrics
        passport = await Collections.passports().find_one({"user_id": user_id})

        # Get sessions count
        sessions_count = await Collections.sessions().count_documents({
            "user_id": user_id,
            "submitted": True,
        })

        # Compute fit score
        user_skill_vector = passport.get("skill_vector", []) if passport else []
        fit_score = compute_job_fit(
            user_vector=user_skill_vector,
            job_vector=job.get("target_vector", []),
        )

        archetype = passport.get("archetype") if passport else None

        applicants.append(ApplicantInfo(
            application_id=application["application_id"],
            user_id=user_id,
            display_name=user.get("display_name", "Unknown"),
            email=user.get("email", ""),
            applied_at=application.get("applied_at", datetime.utcnow()),
            fit_score=round(fit_score, 2),
            archetype=archetype,
            archetype_label=ARCHETYPE_LABELS.get(archetype) if archetype else None,
            sessions_completed=sessions_count,
            metrics=passport.get("metrics", {}) if passport else {},
            status=application.get("status", "pending"),
        ))

    # Sort by fit score descending
    applicants.sort(key=lambda a: -a.fit_score)

    return applicants


@router.get("/job/{job_id}/count")
async def get_applicant_count(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get count of applicants for a job."""
    if current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can view applicant counts",
        )

    count = await Collections.applications().count_documents({"job_id": job_id})
    return {"count": count}
