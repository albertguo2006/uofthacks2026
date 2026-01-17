from fastapi import APIRouter, Depends, Query, HTTPException, status
from datetime import datetime
from typing import Optional
import uuid

from middleware.auth import get_current_user
from db.collections import Collections
from models.job import JobMatch, JobsResponse, UnlockRequirements, JobCreate, RecruiterJob
from services.skillgraph import compute_job_fit

router = APIRouter()


def compute_radar_fit(candidate_radar: dict, job_target_radar: dict) -> float:
    """
    Compute fit score between candidate radar and job requirements.
    Returns 0.0 to 1.0.
    """
    dimensions = ["verification", "velocity", "optimization", "decomposition", "debugging"]

    if not candidate_radar or not job_target_radar:
        return 0.5  # Default neutral score

    candidate_vec = [
        candidate_radar.get(d, {}).get("score", 0.5)
        if isinstance(candidate_radar.get(d), dict)
        else candidate_radar.get(d, 0.5)
        for d in dimensions
    ]
    target_vec = [job_target_radar.get(d, 0.5) for d in dimensions]

    # Weighted cosine similarity (weight by confidence)
    confidence_weights = [
        candidate_radar.get(d, {}).get("confidence", 0.5)
        if isinstance(candidate_radar.get(d), dict)
        else 0.5
        for d in dimensions
    ]

    dot_product = sum(c * t * w for c, t, w in zip(candidate_vec, target_vec, confidence_weights))
    magnitude_c = sum(c**2 * w for c, w in zip(candidate_vec, confidence_weights)) ** 0.5
    magnitude_t = sum(t**2 for t in target_vec) ** 0.5

    if magnitude_c == 0 or magnitude_t == 0:
        return 0.5

    return dot_product / (magnitude_c * magnitude_t)


@router.get("", response_model=JobsResponse)
async def list_jobs(
    include_locked: bool = Query(False, description="Include locked jobs"),
    current_user: dict = Depends(get_current_user),
):
    """Get jobs matching user's skill vector and radar profile."""
    # Get user's passport
    passport = await Collections.passports().find_one({"user_id": current_user["user_id"]})

    user_skill_vector = passport.get("skill_vector", []) if passport else []
    user_metrics = passport.get("metrics", {}) if passport else {}
    user_archetype = passport.get("archetype") if passport else None

    # Get user's radar profile from users collection
    user_doc = await Collections.users().find_one({"_id": current_user["user_id"]})
    user_radar_profile = user_doc.get("radar_profile", {}) if user_doc else {}

    # Get sessions count
    sessions_count = await Collections.sessions().count_documents(
        {"user_id": current_user["user_id"], "submitted": True}
    )

    # Get all jobs
    cursor = Collections.jobs().find({})
    jobs = []

    async for job in cursor:
        # Compute legacy skill vector fit
        skill_vector_fit = compute_job_fit(
            user_vector=user_skill_vector,
            job_vector=job.get("target_vector", []),
        )

        # Compute radar-based fit (if job has target_radar)
        job_target_radar = job.get("target_radar", {})
        radar_fit = compute_radar_fit(user_radar_profile, job_target_radar)

        # Combine scores (weighted average: 40% skill vector, 60% radar)
        # If job has target_radar, use combined score; otherwise use skill vector only
        if job_target_radar:
            fit_score = (skill_vector_fit * 0.4) + (radar_fit * 0.6)
        else:
            fit_score = skill_vector_fit

        # Check if unlocked
        unlocked = True
        missing = []

        # Check minimum fit
        if fit_score < job.get("min_fit", 0):
            unlocked = False
            missing.append(f"need {int(job['min_fit'] * 100)}% fit (you have {int(fit_score * 100)}%)")

        # Check requirements
        must_have = job.get("must_have", {})

        if must_have.get("min_integrity"):
            user_integrity = user_metrics.get("integrity", 0)
            if user_integrity < must_have["min_integrity"]:
                unlocked = False
                missing.append("higher integrity score")

        if must_have.get("min_sessions"):
            if sessions_count < must_have["min_sessions"]:
                unlocked = False
                missing.append(f"complete {must_have['min_sessions']} tasks")

        if must_have.get("required_archetypes"):
            if user_archetype not in must_have["required_archetypes"]:
                unlocked = False
                missing.append(f"be a {' or '.join(must_have['required_archetypes'])}")

        # Skip locked jobs if not requested
        if not unlocked and not include_locked:
            continue

        job_match = JobMatch(
            job_id=job["job_id"],
            title=job["title"],
            company=job["company"],
            tier=job.get("tier", 0),
            fit_score=round(fit_score, 2),
            unlocked=unlocked,
            salary_range=job.get("salary_range", ""),
            location=job.get("location", ""),
            tags=job.get("tags", []),
            description=job.get("description", ""),
        )

        if not unlocked:
            job_match.unlock_requirements = UnlockRequirements(
                min_fit=job.get("min_fit", 0),
                missing=missing,
            )

        jobs.append(job_match)

    # Sort by fit score (unlocked first)
    jobs.sort(key=lambda j: (not j.unlocked, -j.fit_score))

    return JobsResponse(
        jobs=jobs,
        user_skill_vector=user_skill_vector,
        last_updated=datetime.utcnow(),
    )


@router.post("", response_model=RecruiterJob)
async def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new job posting (recruiters only)."""
    if current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can create job postings",
        )

    job_id = f"recruiter-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()

    job_doc = {
        "job_id": job_id,
        "title": job_data.title,
        "description": job_data.description,
        "company": job_data.company,
        "tier": job_data.tier,
        "target_vector": [0.5, 0.5, 0.5, 0.5, 0.5],
        "min_fit": 0.3,
        "must_have": {"min_sessions": 1},
        "salary_range": job_data.salary_range,
        "location": job_data.location,
        "tags": job_data.tags,
        "created_at": now,
        "recruiter_id": current_user["user_id"],
    }

    await Collections.jobs().insert_one(job_doc)

    return RecruiterJob(
        job_id=job_id,
        title=job_data.title,
        description=job_data.description,
        company=job_data.company,
        tier=job_data.tier,
        salary_range=job_data.salary_range,
        location=job_data.location,
        tags=job_data.tags,
        created_at=now,
        recruiter_id=current_user["user_id"],
    )


@router.get("/recruiter", response_model=list[RecruiterJob])
async def list_recruiter_jobs(
    current_user: dict = Depends(get_current_user),
):
    """Get all jobs created by the current recruiter."""
    if current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can access this endpoint",
        )

    cursor = Collections.jobs().find({"recruiter_id": current_user["user_id"]})
    jobs = []

    async for job in cursor:
        jobs.append(
            RecruiterJob(
                job_id=job["job_id"],
                title=job["title"],
                description=job.get("description", ""),
                company=job["company"],
                tier=job.get("tier", 0),
                salary_range=job.get("salary_range", ""),
                location=job.get("location", ""),
                tags=job.get("tags", []),
                created_at=job.get("created_at", datetime.utcnow()),
                recruiter_id=job["recruiter_id"],
            )
        )

    return jobs


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a job posting (owner only)."""
    if current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can delete job postings",
        )

    job = await Collections.jobs().find_one({"job_id": job_id})

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.get("recruiter_id") != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own job postings",
        )

    await Collections.jobs().delete_one({"job_id": job_id})

    return {"message": "Job deleted successfully"}
