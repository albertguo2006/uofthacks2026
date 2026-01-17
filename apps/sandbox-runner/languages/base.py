from abc import ABC, abstractmethod
from typing import Any
import asyncio
import tempfile
import os


class BaseRunner(ABC):
    """Base class for language runners."""

    SANDBOX_DIR = "/tmp/sandbox"

    @abstractmethod
    async def run(self, code: str, input_data: Any, timeout: int) -> dict:
        """Run the code and return results."""
        pass

    async def execute_subprocess(
        self,
        cmd: list[str],
        timeout: int,
        cwd: str = None,
        env: dict = None,
    ) -> tuple[str, str, int]:
        """Execute a subprocess with timeout."""
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or self.SANDBOX_DIR,
            env=process_env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
            return stdout.decode(), stderr.decode(), proc.returncode
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise

    def create_temp_file(self, content: str, suffix: str) -> str:
        """Create a temporary file with the given content."""
        os.makedirs(self.SANDBOX_DIR, exist_ok=True)

        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.SANDBOX_DIR)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            return path
        except:
            os.close(fd)
            raise

    def cleanup_file(self, path: str):
        """Remove a temporary file."""
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except:
            pass
