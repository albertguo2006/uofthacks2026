import asyncio
import json
import os
import tempfile
import shutil
from typing import Any


SANDBOX_DIR = "/tmp/sandbox"


async def run_java(code: str, input_data: Any, timeout: int) -> dict:
    """Execute Java code with the given input."""

    # Create wrapper that handles function execution
    # We need to wrap user code in a class structure
    wrapper = f'''
import java.util.*;
import org.json.JSONObject;
import org.json.JSONArray;

// User code
{code}

class Main {{
    public static void main(String[] args) {{
        try {{
            String inputJson = args[0];

            // Create instance of Solution class and call solve method
            Solution sol = new Solution();
            Object result = sol.solve(inputJson);

            System.out.println("__RESULT__");
            if (result == null) {{
                System.out.println("null");
            }} else if (result instanceof String) {{
                System.out.println("\\"" + result + "\\"");
            }} else {{
                System.out.println(result);
            }}
        }} catch (Exception e) {{
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        }}
    }}
}}
'''

    os.makedirs(SANDBOX_DIR, exist_ok=True)

    # Create temp directory for Java files
    temp_dir = tempfile.mkdtemp(dir=SANDBOX_DIR)
    src_path = os.path.join(temp_dir, "Main.java")

    try:
        with open(src_path, 'w') as f:
            f.write(wrapper)

        # Compile
        proc = await asyncio.create_subprocess_exec(
            'javac', src_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=temp_dir,
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
            'java', '-cp', temp_dir, 'Main', json.dumps(input_data),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=temp_dir,
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
            shutil.rmtree(temp_dir)
        except:
            pass
