from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime
from bson import ObjectId

from middleware.auth import get_current_user
from db.collections import Collections
from models.task import (
    Task,
    TaskSummary,
    TasksResponse,
    TaskSubmission,
    RunResult,
    TestCaseResult,
    SubmitResult,
)
from services.sandbox import execute_code
from services.skillgraph import update_passport_after_submit

router = APIRouter()


@router.get("", response_model=TasksResponse)
async def list_tasks(current_user: dict = Depends(get_current_user)):
    """List all available tasks."""
    cursor = Collections.tasks().find({})
    tasks = []

    async for task in cursor:
        tasks.append(
            TaskSummary(
                task_id=task["task_id"],
                title=task["title"],
                description=task["description"][:200] + "..."
                if len(task["description"]) > 200
                else task["description"],
                difficulty=task["difficulty"],
                category=task["category"],
                language=task["language"],
                estimated_minutes=10
                if task["difficulty"] == "easy"
                else 20
                if task["difficulty"] == "medium"
                else 30,
            )
        )

    return TasksResponse(tasks=tasks)


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str, current_user: dict = Depends(get_current_user)):
    """Get task details with starter code."""
    task = await Collections.tasks().find_one({"task_id": task_id})

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Filter out hidden test cases for response
    visible_test_cases = [
        {"input": tc["input"], "expected_output": tc["expected_output"], "hidden": False}
        for tc in task.get("test_cases", [])
        if not tc.get("hidden", False)
    ]

    return Task(
        task_id=task["task_id"],
        title=task["title"],
        description=task["description"],
        difficulty=task["difficulty"],
        category=task["category"],
        language=task["language"],
        starter_code=task["starter_code"],
        test_cases=visible_test_cases,
        time_limit_seconds=task.get("time_limit_seconds", 5),
    )


@router.post("/{task_id}/run", response_model=RunResult)
async def run_code(
    task_id: str,
    submission: TaskSubmission,
    current_user: dict = Depends(get_current_user),
):
    """Execute code in sandbox and run tests."""
    task = await Collections.tasks().find_one({"task_id": task_id})

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    language = submission.language or task["language"]

    # Execute code against all test cases
    results = []
    total_time_ms = 0
    all_passed = True
    stdout_all = ""
    stderr_all = ""

    for i, test_case in enumerate(task.get("test_cases", [])):
        try:
            result = await execute_code(
                code=submission.code,
                language=language,
                test_input=test_case["input"],
                expected_output=test_case["expected_output"],
                timeout_seconds=task.get("time_limit_seconds", 5),
            )

            is_hidden = test_case.get("hidden", False)
            results.append(
                TestCaseResult(
                    test_case=i + 1,
                    passed=result["passed"],
                    output=result["output"],
                    expected=test_case["expected_output"] if not is_hidden else None,
                    hidden=is_hidden,
                    time_ms=result["time_ms"],
                    error=result.get("error"),
                )
            )

            total_time_ms += result["time_ms"]
            if not result["passed"]:
                all_passed = False

            stdout_all += result.get("stdout", "")
            stderr_all += result.get("stderr", "")

        except Exception as e:
            results.append(
                TestCaseResult(
                    test_case=i + 1,
                    passed=False,
                    output=None,
                    time_ms=0,
                    error=str(e),
                )
            )
            all_passed = False

    return RunResult(
        success=True,
        results=results,
        all_passed=all_passed,
        total_time_ms=total_time_ms,
        stdout=stdout_all,
        stderr=stderr_all,
    )


@router.post("/{task_id}/submit", response_model=SubmitResult)
async def submit_solution(
    task_id: str,
    submission: TaskSubmission,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Submit final solution for evaluation."""
    task = await Collections.tasks().find_one({"task_id": task_id})

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    language = submission.language or task["language"]

    # Run against ALL test cases (including hidden)
    passed_count = 0
    total_count = len(task.get("test_cases", []))

    for test_case in task.get("test_cases", []):
        try:
            result = await execute_code(
                code=submission.code,
                language=language,
                test_input=test_case["input"],
                expected_output=test_case["expected_output"],
                timeout_seconds=task.get("time_limit_seconds", 5),
            )
            if result["passed"]:
                passed_count += 1
        except Exception:
            pass

    passed = passed_count == total_count
    score = int((passed_count / total_count) * 100) if total_count > 0 else 0

    # Update session
    session_doc = {
        "_id": str(ObjectId()),
        "session_id": submission.session_id,
        "user_id": current_user["user_id"],
        "task_id": task_id,
        "started_at": datetime.utcnow(),  # Approximate
        "ended_at": datetime.utcnow(),
        "submitted": True,
        "passed": passed,
        "score": score,
    }

    await Collections.sessions().update_one(
        {"session_id": submission.session_id},
        {"$set": session_doc},
        upsert=True,
    )

    # Update passport in background
    background_tasks.add_task(
        update_passport_after_submit,
        user_id=current_user["user_id"],
        session_id=submission.session_id,
        task_id=task_id,
        passed=passed,
        score=score,
    )

    # Get updated passport info
    passport = await Collections.passports().find_one({"user_id": current_user["user_id"]})

    return SubmitResult(
        submitted=True,
        passed=passed,
        score=score,
        passport_updated=True,
        new_archetype=passport.get("archetype") if passport else None,
        jobs_unlocked=0,  # Will be computed async
    )
