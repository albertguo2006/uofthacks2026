import httpx
import time
from typing import Any
from config import get_settings


async def execute_code(
    code: str,
    language: str,
    test_input: Any,
    expected_output: Any,
    timeout_seconds: int = 5,
) -> dict:
    """Execute code in the sandbox runner and validate output."""
    settings = get_settings()

    start_time = time.time()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.sandbox_runner_url}/run",
                json={
                    "code": code,
                    "language": language,
                    "input": test_input,
                    "timeout": timeout_seconds,
                },
                timeout=timeout_seconds + 5,  # Extra time for network
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return {
                    "passed": False,
                    "output": None,
                    "time_ms": elapsed_ms,
                    "error": f"Sandbox error: {response.text}",
                    "stdout": "",
                    "stderr": response.text,
                }

            result = response.json()

            # Check if execution succeeded
            if result.get("error"):
                return {
                    "passed": False,
                    "output": None,
                    "time_ms": elapsed_ms,
                    "error": result["error"],
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                }

            # Compare output
            actual_output = result.get("output")
            passed = compare_outputs(actual_output, expected_output)

            return {
                "passed": passed,
                "output": actual_output,
                "time_ms": elapsed_ms,
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
            }

    except httpx.TimeoutException:
        return {
            "passed": False,
            "output": None,
            "time_ms": timeout_seconds * 1000,
            "error": "Execution timed out",
            "stdout": "",
            "stderr": "",
        }
    except httpx.ConnectError:
        # Sandbox not available - use fallback execution
        return await execute_code_fallback(
            code, language, test_input, expected_output, timeout_seconds
        )
    except Exception as e:
        return {
            "passed": False,
            "output": None,
            "time_ms": int((time.time() - start_time) * 1000),
            "error": str(e),
            "stdout": "",
            "stderr": "",
        }


def compare_outputs(actual: Any, expected: Any) -> bool:
    """Compare actual output with expected output."""
    # Handle None/null comparison
    if actual is None and expected is None:
        return True
    if actual is None or expected is None:
        return False

    # String comparison (strip whitespace)
    if isinstance(expected, str) and isinstance(actual, str):
        return actual.strip() == expected.strip()

    # Numeric comparison (with tolerance)
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(actual - expected) < 0.0001

    # List comparison
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return False
        return all(compare_outputs(a, e) for a, e in zip(actual, expected))

    # Dict comparison
    if isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected.keys()) != set(actual.keys()):
            return False
        return all(compare_outputs(actual[k], expected[k]) for k in expected)

    # Direct comparison
    return actual == expected


async def execute_code_fallback(
    code: str,
    language: str,
    test_input: Any,
    expected_output: Any,
    timeout_seconds: int = 5,
) -> dict:
    """Fallback execution when sandbox is not available (for development)."""
    import asyncio
    import subprocess
    import json
    import tempfile
    import os

    start_time = time.time()

    try:
        if language == "python":
            # Create test wrapper
            wrapper = f'''
import json
import sys

{code}

# Get the main function name (assumes function is defined)
input_data = json.loads(sys.argv[1])

# Try common function patterns
result = None
if 'processUser' in dir():
    result = processUser(input_data.get('user'))
elif 'process_user' in dir():
    result = process_user(input_data.get('user'))
elif 'main' in dir():
    result = main(input_data)
else:
    # Try to find and call the first defined function
    for name in dir():
        obj = eval(name)
        if callable(obj) and not name.startswith('_'):
            try:
                result = obj(input_data)
                break
            except:
                pass

print(json.dumps(result))
'''

            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(wrapper)
                temp_file = f.name

            try:
                proc = await asyncio.create_subprocess_exec(
                    'python3', temp_file, json.dumps(test_input),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout_seconds
                )

                elapsed_ms = int((time.time() - start_time) * 1000)

                if proc.returncode != 0:
                    return {
                        "passed": False,
                        "output": None,
                        "time_ms": elapsed_ms,
                        "error": stderr.decode(),
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode(),
                    }

                output = json.loads(stdout.decode().strip())
                passed = compare_outputs(output, expected_output)

                return {
                    "passed": passed,
                    "output": output,
                    "time_ms": elapsed_ms,
                    "stdout": "",
                    "stderr": stderr.decode(),
                }

            finally:
                os.unlink(temp_file)

        elif language in ["javascript", "typescript"]:
            # JavaScript execution
            wrapper = f'''
const input = JSON.parse(process.argv[2]);

{code}

let result;
if (typeof processUser === 'function') {{
    result = processUser(input.user);
}} else if (typeof main === 'function') {{
    result = main(input);
}}

console.log(JSON.stringify(result));
'''

            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(wrapper)
                temp_file = f.name

            try:
                proc = await asyncio.create_subprocess_exec(
                    'node', temp_file, json.dumps(test_input),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout_seconds
                )

                elapsed_ms = int((time.time() - start_time) * 1000)

                if proc.returncode != 0:
                    return {
                        "passed": False,
                        "output": None,
                        "time_ms": elapsed_ms,
                        "error": stderr.decode(),
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode(),
                    }

                output = json.loads(stdout.decode().strip())
                passed = compare_outputs(output, expected_output)

                return {
                    "passed": passed,
                    "output": output,
                    "time_ms": elapsed_ms,
                    "stdout": "",
                    "stderr": stderr.decode(),
                }

            finally:
                os.unlink(temp_file)

        else:
            return {
                "passed": False,
                "output": None,
                "time_ms": 0,
                "error": f"Unsupported language: {language}",
                "stdout": "",
                "stderr": "",
            }

    except asyncio.TimeoutError:
        return {
            "passed": False,
            "output": None,
            "time_ms": timeout_seconds * 1000,
            "error": "Execution timed out",
            "stdout": "",
            "stderr": "",
        }
    except Exception as e:
        return {
            "passed": False,
            "output": None,
            "time_ms": int((time.time() - start_time) * 1000),
            "error": str(e),
            "stdout": "",
            "stderr": "",
        }
