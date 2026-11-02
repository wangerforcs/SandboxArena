import json
import subprocess
import sys
import unittest
from pathlib import Path

from arena.schema import validate_result
from arena.workloads import load_workload


ROOT = Path(__file__).resolve().parents[1]


class FrameworkTests(unittest.TestCase):
    def test_workload_is_versioned_and_loadable(self):
        workload = load_workload("python-smoke")
        self.assertEqual(workload["version"], "1.0.0")
        self.assertEqual(len(workload["steps"]), 2)


    def test_cli_runs_and_writes_a_valid_result(self):
        output = ROOT / "data" / "results" / ".test-result.json"
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "arena", "run", "--provider", "mock", "--workload", "python-smoke", "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(validate_result(result), [])
            self.assertEqual(result["measurements"]["status"], "success")
        finally:
            output.unlink(missing_ok=True)


    def test_validator_rejects_secret_like_fields(self):
        result = {
            "schema_version": "1.0",
            "result_id": "x",
            "provider": {"id": "x"},
            "workload": {"id": "x", "version": "1"},
            "run": {"mode": "cold", "region": "x"},
            "environment": {},
            "measurements": {"status": "success", "total_duration_ms": 1},
            "provenance": {"source": "self-run", "api_key": "do-not-submit"},
        }
        self.assertTrue(any("secret-like" in error for error in validate_result(result)))

