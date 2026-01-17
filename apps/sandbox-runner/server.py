from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
import uvicorn

from runner import execute_code

app = FastAPI(
    title="Sandbox Runner",
    description="Isolated code execution service",
    version="1.0.0",
)


class RunRequest(BaseModel):
    code: str
    language: str
    input: Any
    timeout: int = 5


class RunResponse(BaseModel):
    output: Any = None
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    time_ms: int = 0


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sandbox-runner"}


@app.post("/run", response_model=RunResponse)
async def run_code(request: RunRequest):
    """Execute code in a sandboxed environment."""
    try:
        result = await execute_code(
            code=request.code,
            language=request.language,
            input_data=request.input,
            timeout=request.timeout,
        )
        return RunResponse(**result)
    except Exception as e:
        return RunResponse(error=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
