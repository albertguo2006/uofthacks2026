import asyncio
import json
import os
import tempfile
from typing import Any


SANDBOX_DIR = "/tmp/sandbox"


async def run_python(code: str, input_data: Any, timeout: int) -> dict:
    """Execute Python code with the given input."""

    # Create wrapper that handles various function patterns
    wrapper = f'''
import json
import sys

# User code
{code}

# Parse input
input_data = json.loads(sys.argv[1])

# Try to find and execute the main function
result = None
found = False

# Common function names to try
function_names = [
    'processUser', 'process_user',
    'solution', 'solve',
    'main', 'run',
    'two_sum', 'twoSum',
    'three_sum', 'threeSum',
]

# Try each function name
for name in function_names:
    if name in dir() and callable(eval(name)):
        func = eval(name)
        try:
            # Try calling with different argument patterns
            if 'user' in input_data:
                result = func(input_data.get('user'))
            else:
                result = func(input_data)
            found = True
            break
        except TypeError:
            try:
                result = func(**input_data)
                found = True
                break
            except:
                pass

# If no named function found, try to find any defined function
if not found:
    for name in dir():
        if not name.startswith('_') and name not in ['json', 'sys']:
            obj = eval(name)
            if callable(obj):
                try:
                    if 'user' in input_data:
                        result = obj(input_data.get('user'))
                    else:
                        result = obj(input_data)
                    found = True
                    break
                except TypeError:
                    # Try unpacking as keyword arguments
                    try:
                        result = obj(**input_data)
                        found = True
                        break
                    except:
                        pass
                except:
                    pass

print("__RESULT__")
print(json.dumps(result))
'''

    os.makedirs(SANDBOX_DIR, exist_ok=True)

    # Create temp file
    fd, temp_path = tempfile.mkstemp(suffix='.py', dir=SANDBOX_DIR)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(wrapper)

        # Execute
        proc = await asyncio.create_subprocess_exec(
            'python3', temp_path, json.dumps(input_data),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=SANDBOX_DIR,
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )

        stdout_str = stdout.decode()
        stderr_str = stderr.decode()

        if proc.returncode != 0:
            return {
                "output": None,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "error": stderr_str or "Execution failed",
            }

        # Parse result
        output = None
        regular_stdout = ""

        if "__RESULT__" in stdout_str:
            parts = stdout_str.split("__RESULT__")
            regular_stdout = parts[0].strip()
            result_str = parts[1].strip()
            try:
                output = json.loads(result_str)
            except json.JSONDecodeError:
                output = result_str
        else:
            regular_stdout = stdout_str

        return {
            "output": output,
            "stdout": regular_stdout,
            "stderr": stderr_str,
            "error": None,
        }

    finally:
        try:
            os.remove(temp_path)
        except:
            pass
