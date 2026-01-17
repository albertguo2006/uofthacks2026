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
    # Multi-language support
    languages: list[str] = Field(default_factory=list)
    starter_codes: dict[str, str] = Field(default_factory=dict)
    solution_code: Optional[str] = None
    test_cases: list[TestCase]
    time_limit_seconds: int = 5
    # Proctoring support
    proctored: bool = False
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskSummary(BaseModel):
    task_id: str
    title: str
    description: str
    difficulty: str
    category: str
    languages: list[str] = Field(default_factory=list)
    estimated_minutes: int = 10
    proctored: bool = False
    tags: list[str] = Field(default_factory=list)
    passed: Optional[bool] = None


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
    hidden: bool = False
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
