import asyncio
import json
import os
import tempfile
import time
from typing import Any

from languages.python_runner import run_python
from languages.javascript_runner import run_javascript
from languages.typescript_runner import run_typescript
from languages.cpp_runner import run_cpp
from languages.java_runner import run_java

SANDBOX_DIR = "/tmp/sandbox"


async def execute_code(
    code: str,
    language: str,
    input_data: Any,
    timeout: int = 5,
) -> dict:
    """Execute code in the appropriate language runner."""

    # Ensure sandbox directory exists
    os.makedirs(SANDBOX_DIR, exist_ok=True)

    start_time = time.time()

    try:
        if language == "python":
            result = await run_python(code, input_data, timeout)
        elif language == "javascript":
            result = await run_javascript(code, input_data, timeout)
        elif language == "typescript":
            result = await run_typescript(code, input_data, timeout)
        elif language == "cpp":
            result = await run_cpp(code, input_data, timeout)
        elif language == "java":
            result = await run_java(code, input_data, timeout)
        else:
            return {
                "output": None,
                "stdout": "",
                "stderr": "",
                "error": f"Unsupported language: {language}",
                "time_ms": 0,
            }

        elapsed_ms = int((time.time() - start_time) * 1000)
        result["time_ms"] = elapsed_ms
        return result

    except asyncio.TimeoutError:
        return {
            "output": None,
            "stdout": "",
            "stderr": "",
            "error": "Execution timed out",
            "time_ms": timeout * 1000,
        }
    except Exception as e:
        return {
            "output": None,
            "stdout": "",
            "stderr": "",
            "error": str(e),
            "time_ms": int((time.time() - start_time) * 1000),
        }
