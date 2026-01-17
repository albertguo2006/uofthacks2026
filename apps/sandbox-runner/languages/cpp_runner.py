import asyncio
import json
import os
import tempfile
from typing import Any


SANDBOX_DIR = "/tmp/sandbox"


async def run_cpp(code: str, input_data: Any, timeout: int) -> dict:
    """Execute C++ code with the given input."""

    # Create wrapper that handles function execution
    wrapper = f'''
#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <algorithm>
#include <cmath>
#include <cstdlib>

// Simple JSON parsing helpers
std::string trim(const std::string& s) {{
    size_t start = s.find_first_not_of(" \\t\\n\\r");
    size_t end = s.find_last_not_of(" \\t\\n\\r");
    return (start == std::string::npos) ? "" : s.substr(start, end - start + 1);
}}

// User code
{code}

int main(int argc, char* argv[]) {{
    std::string input_json = argv[1];

    // Call the solution function
    // The user's code should define a solution() function
    auto result = solution(input_json);

    std::cout << "__RESULT__" << std::endl;
    std::cout << result << std::endl;

    return 0;
}}
'''

    os.makedirs(SANDBOX_DIR, exist_ok=True)

    # Create temp files
    fd_src, src_path = tempfile.mkstemp(suffix='.cpp', dir=SANDBOX_DIR)
    exe_path = src_path.replace('.cpp', '')

    try:
        with os.fdopen(fd_src, 'w') as f:
            f.write(wrapper)

        # Compile
        proc = await asyncio.create_subprocess_exec(
            'g++', '-std=c++17', '-O2', '-o', exe_path, src_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=SANDBOX_DIR,
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )

        if proc.returncode != 0:
            return {
                "output": None,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "error": f"Compilation failed: {stderr.decode()}",
            }

        # Execute
        proc = await asyncio.create_subprocess_exec(
            exe_path, json.dumps(input_data),
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
            os.remove(src_path)
        except:
            pass
        try:
            os.remove(exe_path)
        except:
            pass
