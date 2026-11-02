"""Local provider used to verify the framework without vendor accounts."""

from __future__ import annotations

import subprocess
import sys
import time
import uuid
from typing import Sequence

from .base import SandboxHandle


class MockLocalProvider:
    id = "mock-local"

    def create(self, workload: dict) -> SandboxHandle:
        return SandboxHandle(self.id, f"local-{uuid.uuid4().hex[:12]}")

    def execute(self, handle: SandboxHandle, command: Sequence[str], timeout_seconds: int) -> dict:
        started = time.perf_counter_ns()
        completed = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        duration_ms = (time.perf_counter_ns() - started) / 1_000_000
        return {
            "status": "success" if completed.returncode == 0 else "failure",
            "exit_code": completed.returncode,
            "duration_ms": round(duration_ms, 3),
            "stdout": completed.stdout[-2000:],
            "stderr": completed.stderr[-2000:],
        }

    def destroy(self, handle: SandboxHandle) -> None:
        return None


def python_command(code: str) -> list[str]:
    return [sys.executable, "-c", code]

