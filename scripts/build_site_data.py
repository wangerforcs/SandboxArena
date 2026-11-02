#!/usr/bin/env python3
"""Build the browser-facing data file from reviewed result observations."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arena.schema import load_json, validate_result  # noqa: E402


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 3)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * weight, 3)


def samples_for(result: dict[str, Any]) -> list[dict[str, Any]]:
    measurements = result["measurements"]
    repetitions = measurements.get("repetitions")
    if isinstance(repetitions, list) and repetitions:
        return [item for item in repetitions if isinstance(item, dict)]
    return [{
        "status": measurements["status"],
        "total_duration_ms": measurements["total_duration_ms"],
    }]


def summarize_result(result: dict[str, Any], filename: str) -> dict[str, Any]:
    samples = samples_for(result)
    durations = [float(item["total_duration_ms"]) for item in samples if isinstance(item.get("total_duration_ms"), (int, float))]
    successes = sum(item.get("status") == "success" for item in samples)
    measurements = result["measurements"]
    return {
        "result_id": result["result_id"],
        "filename": filename,
        "provider": result["provider"].get("id", "unknown"),
        "workload": result["workload"].get("id", "unknown"),
        "workload_title": result["workload"].get("title", result["workload"].get("id", "unknown")),
        "workload_version": result["workload"].get("version"),
        "mode": result["run"].get("mode", "unknown"),
        "region": result["run"].get("region", "unknown"),
        "source": result["provenance"].get("source", "unknown"),
        "status": measurements["status"],
        "success_rate": round(successes / len(samples), 4) if samples else 0,
        "sample_count": len(samples),
        "avg_duration_ms": round(statistics.fmean(durations), 3) if durations else None,
        "p50_duration_ms": percentile(durations, 0.50),
        "p95_duration_ms": percentile(durations, 0.95),
        "estimated_cost_usd": measurements.get("estimated_cost_usd"),
        "started_at": result["run"].get("started_at"),
    }


def build(results_dir: Path) -> dict[str, Any]:
    records = []
    errors = []
    for path in sorted(results_dir.glob("*.json")):
        try:
            result = load_json(path)
            validation_errors = validate_result(result)
            if validation_errors:
                errors.append(f"{path}: " + "; ".join(validation_errors))
                continue
            records.append(summarize_result(result, path.name))
        except (OSError, json.JSONDecodeError, ValueError, KeyError) as error:
            errors.append(f"{path}: {error}")

    if errors:
        raise ValueError("invalid result files:\n" + "\n".join(errors))

    providers = sorted({record["provider"] for record in records})
    workloads = sorted({record["workload"] for record in records})
    source_counts: dict[str, int] = {}
    for record in records:
        source_counts[record["source"]] = source_counts.get(record["source"], 0) + 1

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "result_count": len(records),
            "provider_count": len(providers),
            "workload_count": len(workloads),
            "success_rate": round(statistics.fmean(record["success_rate"] for record in records), 4) if records else None,
            "sources": source_counts,
        },
        "providers": providers,
        "workloads": workloads,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=ROOT / "data" / "results")
    parser.add_argument("--output", type=Path, default=ROOT / "web" / "data" / "results.json")
    args = parser.parse_args()
    payload = build(args.results_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(payload['records'])} result records -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

