import asyncio
import json
import os
import tempfile
from typing import Any


SANDBOX_DIR = "/tmp/sandbox"


async def run_javascript(code: str, input_data: Any, timeout: int) -> dict:
    """Execute JavaScript code with the given input."""

    # Create wrapper that handles various function patterns
    wrapper = f'''
const inputData = JSON.parse(process.argv[2]);

// User code
{code}

// Try to find and execute the main function
let result = undefined;
let found = false;

// Common function names to try
const functionNames = [
    'processUser', 'process_user',
    'solution', 'solve',
    'main', 'run',
];

// Try each function name
for (const name of functionNames) {{
    if (typeof global[name] === 'function' || typeof eval(name) === 'function') {{
        try {{
            const func = typeof global[name] === 'function' ? global[name] : eval(name);
            if (inputData.user !== undefined) {{
                result = func(inputData.user);
            }} else {{
                result = func(inputData);
            }}
            found = true;
            break;
        }} catch (e) {{
            // Try next
        }}
    }}
}}

// Check for module.exports
if (!found && typeof module !== 'undefined' && module.exports) {{
    const exported = module.exports;
    for (const name of functionNames) {{
        if (typeof exported[name] === 'function') {{
            try {{
                if (inputData.user !== undefined) {{
                    result = exported[name](inputData.user);
                }} else {{
                    result = exported[name](inputData);
                }}
                found = true;
                break;
            }} catch (e) {{
                // Try next
            }}
        }}
    }}

    // Try first exported function
    if (!found) {{
        for (const key of Object.keys(exported)) {{
            if (typeof exported[key] === 'function') {{
                try {{
                    if (inputData.user !== undefined) {{
                        result = exported[key](inputData.user);
                    }} else {{
                        result = exported[key](inputData);
                    }}
                    found = true;
                    break;
                }} catch (e) {{
                    // Try next
                }}
            }}
        }}
    }}
}}

console.log("__RESULT__");
console.log(JSON.stringify(result));
'''

    os.makedirs(SANDBOX_DIR, exist_ok=True)

    # Create temp file
    fd, temp_path = tempfile.mkstemp(suffix='.js', dir=SANDBOX_DIR)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(wrapper)

        # Execute
        proc = await asyncio.create_subprocess_exec(
            'node', temp_path, json.dumps(input_data),
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
