"""Run a versioned workload through a provider adapter."""

from __future__ import annotations

import platform
import socket
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from .providers.base import ProviderAdapter


def run_workload(
    provider: ProviderAdapter,
    workload: dict[str, Any],
    *,
    repetitions: int = 1,
    mode: str = "cold",
    region: str = "local",
    source: str = "self-run",
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    if repetitions < 1:
        raise ValueError("repetitions must be >= 1")

    observations = []
    for repetition in range(repetitions):
        started_at = time.perf_counter_ns()
        handle = provider.create(workload)
        provision_ms = (time.perf_counter_ns() - started_at) / 1_000_000
        steps = []
        try:
            for step in workload["steps"]:
                step_result = provider.execute(handle, step["command"], timeout_seconds)
                steps.append({
                    "id": step["id"],
                    "status": step_result["status"],
                    "duration_ms": step_result["duration_ms"],
                    "exit_code": step_result.get("exit_code"),
                })
                if step_result["status"] != "success":
                    break
            status = "success" if steps and all(step["status"] == "success" for step in steps) else "failure"
        finally:
            provider.destroy(handle)
        total_ms = (time.perf_counter_ns() - started_at) / 1_000_000
        observations.append({
            "repetition": repetition + 1,
            "status": status,
            "provision_ms": round(provision_ms, 3),
            "total_duration_ms": round(total_ms, 3),
            "steps": steps,
        })

    successful = [item for item in observations if item["status"] == "success"]
    totals = [item["total_duration_ms"] for item in observations]
    return {
        "schema_version": "1.0",
        "result_id": str(uuid.uuid4()),
        "provider": {
            "id": provider.id,
            "adapter_version": "0.1.0",
        },
        "workload": {
            "id": workload["id"],
            "version": workload["version"],
            "title": workload["title"],
        },
        "run": {
            "mode": mode,
            "region": region,
            "repetitions": repetitions,
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
        "environment": {
            "runner_hostname": socket.gethostname(),
            "os": platform.system().lower(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
        },
        "measurements": {
            "status": "success" if len(successful) == repetitions else "partial" if successful else "failure",
            "success_rate": round(len(successful) / repetitions, 4),
            "total_duration_ms": round(sum(totals) / len(totals), 3),
            "repetitions": observations,
        },
        "provenance": {
            "source": source,
            "runner": "sandbox-arena-cli/0.1.0",
            "raw_trace_included": False,
        },
    }

