"""Command line interface for Sandbox Arena."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .providers.mock import MockLocalProvider
from .runner import run_workload
from .schema import load_json, validate_result
from .workloads import list_workloads, load_workload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arena", description="Workload-centric Agent Sandbox benchmark runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-workloads", help="list available workloads")

    run = subparsers.add_parser("run", help="run a workload")
    run.add_argument("--provider", required=True, choices=["mock"], help="provider adapter")
    run.add_argument("--workload", required=True)
    run.add_argument("--repetitions", type=int, default=1)
    run.add_argument("--mode", choices=["cold", "warm", "resume"], default="cold")
    run.add_argument("--region", default="local")
    run.add_argument("--timeout-seconds", type=int, default=120)
    run.add_argument("--output", type=Path)

    validate = subparsers.add_parser("validate", help="validate a result JSON file")
    validate.add_argument("path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "list-workloads":
        for workload in list_workloads():
            print(f"{workload['id']}\t{workload['version']}\t{workload['title']}")
        return 0

    if args.command == "validate":
        errors = validate_result(load_json(args.path))
        if errors:
            print("INVALID")
            for error in errors:
                print(f"- {error}")
            return 1
        print("VALID")
        return 0

    if args.command == "run":
        workload = load_workload(args.workload)
        result = run_workload(
            MockLocalProvider(),
            workload,
            repetitions=args.repetitions,
            mode=args.mode,
            region=args.region,
            timeout_seconds=args.timeout_seconds,
        )
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0 if result["measurements"]["status"] == "success" else 1

    return 2

