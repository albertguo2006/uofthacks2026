from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class TestCase(BaseModel):
    input: Any
    expected_output: Any
    hidden: bool = False


class Task(BaseModel):
    task_id: str
    title: str
    description: str
    difficulty: str = Field(pattern="^(easy|medium|hard)$")
    category: str = Field(pattern="^(bugfix|refactor|feature|optimization)$")
    language: str = Field(pattern="^(python|javascript|typescript|cpp|java)$")
    starter_code: str
    solution_code: Optional[str] = None
    test_cases: list[TestCase]
    time_limit_seconds: int = 5
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskSummary(BaseModel):
    task_id: str
    title: str
    description: str
    difficulty: str
    category: str
    language: str
    estimated_minutes: int = 10


class TasksResponse(BaseModel):
    tasks: list[TaskSummary]


class TaskSubmission(BaseModel):
    session_id: str
    code: str
    language: Optional[str] = None


class TestCaseResult(BaseModel):
    test_case: int
    passed: bool
    output: Any
    expected: Any = None
    time_ms: int
    error: Optional[str] = None


class RunResult(BaseModel):
    success: bool
    results: list[TestCaseResult]
    all_passed: bool
    total_time_ms: int
    stdout: str = ""
    stderr: str = ""


class SubmitResult(BaseModel):
    submitted: bool
    passed: bool
    score: int
    passport_updated: bool
    new_archetype: Optional[str] = None
    jobs_unlocked: int = 0
