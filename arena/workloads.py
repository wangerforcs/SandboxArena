"""Versioned workload catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_WORKLOAD_DIR = Path(__file__).resolve().parent.parent / "workloads"


def list_workloads(directory: Path = DEFAULT_WORKLOAD_DIR) -> list[dict[str, Any]]:
    workloads = []
    for path in sorted(directory.glob("*/workload.json")):
        with path.open("r", encoding="utf-8") as handle:
            workload = json.load(handle)
        workload["_path"] = str(path)
        workloads.append(workload)
    return workloads


def load_workload(workload_id: str, directory: Path = DEFAULT_WORKLOAD_DIR) -> dict[str, Any]:
    for workload in list_workloads(directory):
        if workload.get("id") == workload_id:
            return workload
    available = ", ".join(item.get("id", "?") for item in list_workloads(directory)) or "none"
    raise ValueError(f"unknown workload {workload_id!r}; available: {available}")

