from fastapi import APIRouter, HTTPException, status, Depends, Request

from middleware.auth import get_current_user
from db.collections import Collections
from models.passport import (
    SkillPassport,
    Archetype,
    PassportMetrics,
    NotableMoment,
    InterviewInfo,
    InterviewHighlight,
)

router = APIRouter()

# Archetype definitions
ARCHETYPES = {
    "fast_iterator": {
        "label": "Fast Iterator",
        "description": "Rapid prototyper who values quick feedback cycles and iterative improvement",
    },
    "careful_tester": {
        "label": "Careful Tester",
        "description": "Prioritizes test coverage and validation before shipping",
    },
    "debugger": {
        "label": "Systematic Debugger",
        "description": "Methodical problem-solver who excels at tracking down issues",
    },
    "craftsman": {
        "label": "Code Craftsman",
        "description": "Focuses on clean, maintainable code with attention to detail",
    },
    "explorer": {
        "label": "Explorer",
        "description": "Creative problem-solver who tries multiple approaches",
    },
}

# Mock passport data for Jane Candidate in dev mode
MOCK_JANE_PASSPORT = SkillPassport(
    user_id="dev-candidate-123",
    display_name="Jane Candidate",
    archetype=Archetype(
        name="craftsman",
        label="Code Craftsman",
        description="Focuses on clean, maintainable code with attention to detail",
        confidence=0.87,
    ),
    skill_vector=[0.85, 0.78, 0.72, 0.68, 0.65, 0.82, 0.75, 0.80],
    metrics=PassportMetrics(
        iteration_velocity=0.72,
        debug_efficiency=0.85,
        craftsmanship=0.91,
        tool_fluency=0.78,
        integrity=1.0,
    ),
    sessions_completed=12,
    tasks_passed=10,
    notable_moments=[
        NotableMoment(
            type="achievement",
            description="Solved complex async race condition in under 5 minutes",
            session_id="session-001",
        ),
        NotableMoment(
            type="insight",
            description="Identified edge case that wasn't in the test suite",
            session_id="session-003",
        ),
        NotableMoment(
            type="achievement",
            description="Refactored legacy code with zero regressions",
            session_id="session-007",
        ),
    ],
    interview=InterviewInfo(
        has_video=True,
        video_id="mock-video-123",
        highlights=[
            InterviewHighlight(
                timestamp="02:34",
                description="Explained approach to debugging systematically",
                query="debugging methodology",
            ),
            InterviewHighlight(
                timestamp="08:15",
                description="Discussed trade-offs in architecture decisions",
                query="system design",
            ),
        ],
    ),
)


@router.get("/{user_id}", response_model=SkillPassport)
async def get_passport(user_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """Get a user's skill passport."""
    # Check for dev mode - return mock data
    dev_mode = request.headers.get("X-Dev-Mode")
    if dev_mode == "true":
        if user_id == "dev-candidate-123" or current_user["user_id"] == "dev-candidate-123":
            return MOCK_JANE_PASSPORT
        # For any other user in dev mode, return a basic passport
        return SkillPassport(
            user_id=user_id,
            display_name=f"Dev User {user_id}",
        )
    
    # Allow viewing own passport or if recruiter
    if current_user["user_id"] != user_id and current_user["role"] != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this passport",
        )

    # Get user info
    user = await Collections.users().find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get passport
    passport = await Collections.passports().find_one({"user_id": user_id})
    if not passport:
        # Return empty passport
        return SkillPassport(
            user_id=user_id,
            display_name=user.get("display_name", ""),
        )

    # Get session stats
    sessions_completed = await Collections.sessions().count_documents(
        {"user_id": user_id, "submitted": True}
    )
    tasks_passed = await Collections.sessions().count_documents(
        {"user_id": user_id, "passed": True}
    )

    # Build archetype info
    archetype = None
    if passport.get("archetype"):
        archetype_info = ARCHETYPES.get(passport["archetype"], {})
        archetype = Archetype(
            name=passport["archetype"],
            label=archetype_info.get("label", passport["archetype"]),
            description=archetype_info.get("description", ""),
            confidence=passport.get("archetype_confidence", 0.0),
        )

    # Build metrics
    metrics_data = passport.get("metrics", {})
    metrics = PassportMetrics(
        iteration_velocity=metrics_data.get("iteration_velocity", 0.0),
        debug_efficiency=metrics_data.get("debug_efficiency", 0.0),
        craftsmanship=metrics_data.get("craftsmanship", 0.0),
        tool_fluency=metrics_data.get("tool_fluency", 0.0),
        integrity=metrics_data.get("integrity", 1.0),
    )

    # Build notable moments
    notable_moments = [
        NotableMoment(
            type=m.get("type", "achievement"),
            description=m.get("highlight", m.get("description", "")),
            session_id=m.get("session_id"),
            timestamp=m.get("timestamp"),
        )
        for m in passport.get("notable_sessions", [])
    ]

    # Build interview info
    interview = InterviewInfo(has_video=False)
    if passport.get("interview_video_id"):
        interview = InterviewInfo(
            has_video=True,
            video_id=passport.get("interview_video_id"),
            highlights=[
                InterviewHighlight(
                    timestamp=f"{int(h['timestamp_start'] // 60):02d}:{int(h['timestamp_start'] % 60):02d}",
                    description=h.get("description", ""),
                    query=h.get("query_matched", ""),
                )
                for h in passport.get("interview_highlights", [])
            ],
        )

    return SkillPassport(
        user_id=user_id,
        display_name=user.get("display_name", ""),
        archetype=archetype,
        skill_vector=passport.get("skill_vector", []),
        metrics=metrics,
        sessions_completed=sessions_completed,
        tasks_passed=tasks_passed,
        notable_moments=notable_moments,
        interview=interview,
        updated_at=passport.get("updated_at"),
    )


@router.get("/me", response_model=SkillPassport)
async def get_my_passport(request: Request, current_user: dict = Depends(get_current_user)):
    """Get the current user's skill passport."""
    return await get_passport(current_user["user_id"], request, current_user)


@router.get("/{user_id}/proficiencies")
async def get_skill_proficiencies(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a user's skill proficiencies."""
    # Allow viewing own proficiencies or if recruiter
    if current_user["user_id"] != user_id and current_user.get("role") != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these proficiencies",
        )

    prof_doc = await Collections.skill_proficiencies().find_one({"user_id": user_id})

    if not prof_doc:
        return {"proficiencies": []}

    # Convert dict to list for frontend
    proficiencies = []
    for key, prof in prof_doc.get("proficiencies", {}).items():
        proficiencies.append({
            "name": prof.get("name", key),
            "score": prof.get("score", 0.0),
            "tasks_completed": prof.get("tasks_completed", 0),
        })

    # Sort by score descending
    proficiencies.sort(key=lambda x: x["score"], reverse=True)

    return {"proficiencies": proficiencies}
