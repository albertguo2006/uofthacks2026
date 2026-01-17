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
from services.amplitude import forward_to_amplitude
from services.skillgraph import update_passport_after_submit

router = APIRouter()


@router.get("", response_model=TasksResponse)
async def list_tasks(current_user: dict = Depends(get_current_user)):
    """List all available tasks."""
    # Fetch user's completion status for all tasks
    user_completions = {}
    saved_cursor = Collections.saved_code().find({"user_id": current_user["user_id"]})
    async for saved in saved_cursor:
        user_completions[saved["task_id"]] = saved.get("passed", False)

    cursor = Collections.tasks().find({})
    tasks = []

    async for task in cursor:
        is_proctored = task.get("proctored", False)
        task_completed = user_completions.get(task["task_id"]) is True

        # For proctored tasks, hide description until session starts (unless completed)
        if is_proctored and not task_completed:
            title = "[PROCTORED TASK]"
            description = "Start proctored session to view task details"
        else:
            title = task["title"]
            description = (
                task["description"][:200] + "..."
                if len(task["description"]) > 200
                else task["description"]
            )

        # Handle both legacy (language) and new (languages) format
        languages = task.get("languages", [])
        if not languages and "language" in task:
            languages = [task["language"]]

        tasks.append(
            TaskSummary(
                task_id=task["task_id"],
                title=title,
                description=description,
                difficulty=task["difficulty"],
                category=task["category"],
                languages=languages,
                estimated_minutes=10
                if task["difficulty"] == "easy"
                else 20
                if task["difficulty"] == "medium"
                else 30,
                proctored=is_proctored,
                tags=task.get("tags", []),
                passed=user_completions.get(task["task_id"]),
            )
        )

    return TasksResponse(tasks=tasks)


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    proctoring_session_id: str = None,
    current_user: dict = Depends(get_current_user),
):
    """Get task details with starter code."""
    task = await Collections.tasks().find_one({"task_id": task_id})

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # For proctored tasks, verify active proctoring session
    if task.get("proctored", False):
        if not proctoring_session_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Proctored task requires active proctoring session",
            )

        session = await Collections.proctoring_sessions().find_one({
            "session_id": proctoring_session_id,
            "user_id": current_user["user_id"],
            "task_id": task_id,
            "status": "active",
        })

        if not session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or inactive proctoring session",
            )

    # Filter out hidden test cases for response
    visible_test_cases = [
        {"input": tc["input"], "expected_output": tc["expected_output"], "hidden": False}
        for tc in task.get("test_cases", [])
        if not tc.get("hidden", False)
    ]

    # Handle both legacy (language/starter_code) and new (languages/starter_codes) format
    languages = task.get("languages", [])
    starter_codes = task.get("starter_codes", {})

    if not languages and "language" in task:
        languages = [task["language"]]
    if not starter_codes and "starter_code" in task:
        lang = task.get("language", "javascript")
        starter_codes = {lang: task["starter_code"]}

    return Task(
        task_id=task["task_id"],
        title=task["title"],
        description=task["description"],
        difficulty=task["difficulty"],
        category=task["category"],
        languages=languages,
        starter_codes=starter_codes,
        test_cases=visible_test_cases,
        time_limit_seconds=task.get("time_limit_seconds", 5),
        proctored=task.get("proctored", False),
        tags=task.get("tags", []),
    )


@router.post("/{task_id}/run", response_model=RunResult)
async def run_code(
    task_id: str,
    submission: TaskSubmission,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Execute code in sandbox and run tests."""
    task = await Collections.tasks().find_one({"task_id": task_id})

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    language = submission.language or task.get("language", "python")

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

    tests_passed = sum(1 for result in results if result.passed)
    tests_total = len(results)

    event_id = str(ObjectId())
    event_doc = {
        "_id": event_id,
        "user_id": current_user["user_id"],
        "session_id": submission.session_id,
        "task_id": task_id,
        "event_type": "test_cases_ran",
        "timestamp": datetime.utcnow(),
        "properties": {
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "runtime_ms": total_time_ms,
            "result": "pass" if all_passed else "fail",
        },
        "forwarded_to_amplitude": False,
        "processed_for_ml": False,
    }

    await Collections.events().insert_one(event_doc)
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=current_user["user_id"],
        event_type="test_cases_ran",
        timestamp=int(event_doc["timestamp"].timestamp() * 1000),
        properties={
            "session_id": submission.session_id,
            "task_id": task_id,
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "runtime_ms": total_time_ms,
            "result": "pass" if all_passed else "fail",
        },
    )

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

    language = submission.language or task.get("language", "python")

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

    event_id = str(ObjectId())
    event_doc = {
        "_id": event_id,
        "user_id": current_user["user_id"],
        "session_id": submission.session_id,
        "task_id": task_id,
        "event_type": "task_submitted",
        "timestamp": datetime.utcnow(),
        "properties": {
            "tests_passed": passed_count,
            "tests_total": total_count,
            "passed": passed,
            "score": score,
        },
        "forwarded_to_amplitude": False,
        "processed_for_ml": False,
    }

    await Collections.events().insert_one(event_doc)
    background_tasks.add_task(
        forward_to_amplitude,
        event_id=event_id,
        user_id=current_user["user_id"],
        event_type="task_submitted",
        timestamp=int(event_doc["timestamp"].timestamp() * 1000),
        properties={
            "session_id": submission.session_id,
            "task_id": task_id,
            "tests_passed": passed_count,
            "tests_total": total_count,
            "passed": passed,
            "score": score,
        },
    )

    # Save the submitted code to user's saved_code collection
    await Collections.saved_code().update_one(
        {"user_id": current_user["user_id"], "task_id": task_id},
        {
            "$set": {
                "user_id": current_user["user_id"],
                "task_id": task_id,
                "code": submission.code,
                "language": language,
                "submitted_at": datetime.utcnow(),
                "passed": passed,
                "score": score,
            }
        },
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


@router.get("/{task_id}/saved-code")
async def get_saved_code(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get user's previously saved code for a task."""
    saved = await Collections.saved_code().find_one(
        {"user_id": current_user["user_id"], "task_id": task_id}
    )

    if not saved:
        return {"code": None}

    return {
        "code": saved.get("code"),
        "language": saved.get("language"),
        "submitted_at": saved.get("submitted_at"),
        "passed": saved.get("passed"),
        "score": saved.get("score"),
    }
