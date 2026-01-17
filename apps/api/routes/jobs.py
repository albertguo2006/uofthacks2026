from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import Optional

from middleware.auth import get_current_user
from db.collections import Collections
from models.job import JobMatch, JobsResponse, UnlockRequirements
from services.skillgraph import compute_job_fit

router = APIRouter()


@router.get("", response_model=JobsResponse)
async def list_jobs(
    include_locked: bool = Query(False, description="Include locked jobs"),
    current_user: dict = Depends(get_current_user),
):
    """Get jobs matching user's skill vector."""
    # Get user's passport
    passport = await Collections.passports().find_one({"user_id": current_user["user_id"]})

    user_skill_vector = passport.get("skill_vector", []) if passport else []
    user_metrics = passport.get("metrics", {}) if passport else {}
    user_archetype = passport.get("archetype") if passport else None

    # Get sessions count
    sessions_count = await Collections.sessions().count_documents(
        {"user_id": current_user["user_id"], "submitted": True}
    )

    # Get all jobs
    cursor = Collections.jobs().find({})
    jobs = []

    async for job in cursor:
        # Compute fit score
        fit_score = compute_job_fit(
            user_vector=user_skill_vector,
            job_vector=job.get("target_vector", []),
        )

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
