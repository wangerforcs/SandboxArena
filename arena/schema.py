"""Validation and small helpers for benchmark observations.

The first version intentionally uses the Python standard library only. The
JSON Schema file is the public contract; this module provides a dependency-free
validator for the fields that matter to the CLI and GitHub workflow.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "schema_version",
    "result_id",
    "provider",
    "workload",
    "run",
    "environment",
    "measurements",
    "provenance",
}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("result must be a JSON object")
    return value


def validate_result(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - result.keys())
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")

    if result.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")

    _require_string(result, "result_id", errors)
    for section in ("provider", "workload", "run", "environment", "measurements", "provenance"):
        if not isinstance(result.get(section), dict):
            errors.append(f"{section} must be an object")

    _require_string(result.get("provider", {}), "id", errors, prefix="provider.")
    _require_string(result.get("workload", {}), "id", errors, prefix="workload.")
    _require_string(result.get("workload", {}), "version", errors, prefix="workload.")
    _require_string(result.get("run", {}), "mode", errors, prefix="run.")
    _require_string(result.get("run", {}), "region", errors, prefix="run.")
    _require_string(result.get("provenance", {}), "source", errors, prefix="provenance.")

    source = result.get("provenance", {}).get("source")
    allowed_sources = {"self-run", "community-run", "vendor-reported", "official-claim"}
    if source is not None and source not in allowed_sources:
        errors.append(f"provenance.source must be one of: {', '.join(sorted(allowed_sources))}")

    measurements = result.get("measurements", {})
    for field in ("status", "total_duration_ms"):
        if field not in measurements:
            errors.append(f"measurements.{field} is required")
    if measurements.get("status") not in {"success", "failure", "partial"}:
        errors.append("measurements.status must be success, failure, or partial")
    if not _is_non_negative_number(measurements.get("total_duration_ms")):
        errors.append("measurements.total_duration_ms must be a non-negative number")

    if "steps" in measurements and not isinstance(measurements["steps"], list):
        errors.append("measurements.steps must be an array")
    if "estimated_cost_usd" in measurements and not _is_non_negative_number(measurements["estimated_cost_usd"]):
        errors.append("measurements.estimated_cost_usd must be a non-negative number")

    # Secrets should never enter a public result file.
    serialized = json.dumps(result, ensure_ascii=False).lower()
    for suspicious in ("api_key", "apikey", "access_token", "secret_key", "authorization: bearer"):
        if suspicious in serialized:
            errors.append(f"result appears to contain a secret-like field: {suspicious}")

    return errors


def _require_string(value: Any, field: str, errors: list[str], prefix: str = "") -> None:
    if not isinstance(value, dict) or not isinstance(value.get(field), str) or not value[field]:
        errors.append(f"{prefix}{field} must be a non-empty string")


def _is_non_negative_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0

