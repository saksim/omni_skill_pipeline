from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "internal_launch_gate.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _launch_gate_report(*, decision: str = "HOLD", failed_checks: list[str] | None = None) -> dict[str, object]:
    failed = ["trial_loop_volume_and_modality_coverage"] if failed_checks is None else failed_checks
    return {
        "schema_version": "broad_launch_readiness.v1",
        "decision": decision,
        "failed_checks": failed,
        "checks": [{"id": check_id, "status": "fail", "blocking": True} for check_id in failed],
    }


def _trial_metrics_report(*, unreviewed_published_count: int = 0) -> dict[str, object]:
    return {
        "trial_metrics": {
            "safety": {
                "unreviewed_published_count": unreviewed_published_count,
                "critical_secret_or_pii_leak_count": 0,
                "high_severity_incident_count": 0,
            }
        }
    }


def _controlled_trial_run_report(*, fixture: bool = True, force_review_mode: bool = True) -> dict[str, object]:
    return {
        "sample_count": 1,
        "use_fixture_stubs": fixture,
        "force_review_mode": force_review_mode,
        "samples": [
            {
                "sample_id": "sample-1",
                "loop_metrics": {
                    "status": "complete",
                    "evidence_origin": "fixture" if fixture else "real",
                    "published_without_review": False,
                },
            }
        ],
    }


def _health_report(status: str = "ready", http_status: int = 200) -> dict[str, object]:
    return {"status": status, "http_status": http_status, "checks": []}


def _create_repo_fixture(
    root: Path,
    *,
    workflow_script: str = "scripts/ci.py",
    launch_failed_checks: list[str] | None = None,
    health_status: str = "ready",
    health_http_status: int = 200,
) -> Path:
    _write_text(
        root / ".github" / "workflows" / "ci.yml",
        "name: CI\njobs:\n  test:\n    steps:\n      - run: python %s --coverage-fail-under 50\n" % workflow_script,
    )
    _write_text(root / "scripts" / "ci.py", "print('ci placeholder')\n")
    _write_text(
        root / "docs" / "INDEX.md",
        "\n".join(
            [
                "- working/status/2026-06-18-internal-dogfood-launch-construction-plan.md",
                "- working/status/internal-dogfood-launch/README.md",
            ]
        )
        + "\n",
    )
    baseline_root = root / "docs" / "working" / "status" / "baselines"
    _write_json(baseline_root / "broad-launch-readiness-report.json", _launch_gate_report(failed_checks=launch_failed_checks))
    _write_json(
        baseline_root / "controlled-trial" / "trial-metrics-report.json",
        _trial_metrics_report(),
    )
    _write_json(
        baseline_root / "controlled-trial" / "controlled-trial-run-report.json",
        _controlled_trial_run_report(),
    )
    health_path = baseline_root / "internal-dogfood-api-health-report.json"
    _write_json(health_path, _health_report(status=health_status, http_status=health_http_status))
    return health_path


def _run_gate(root: Path, *extra_args: str) -> tuple[int, dict[str, object], str]:
    output_path = root / "internal-dogfood-report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(root),
            "--healthz-report",
            str(root / "docs" / "working" / "status" / "baselines" / "internal-dogfood-api-health-report.json"),
            "--output",
            str(output_path),
            "--summary-output",
            "-",
            "--ci-result",
            "passed",
            *extra_args,
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(output_path.read_text(encoding="utf-8")) if output_path.is_file() else {}
    return completed.returncode, report, completed.stdout + completed.stderr


def _run_gate_without_ci_result(root: Path) -> tuple[int, dict[str, object], str]:
    output_path = root / "internal-dogfood-report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(root),
            "--healthz-report",
            str(root / "docs" / "working" / "status" / "baselines" / "internal-dogfood-api-health-report.json"),
            "--output",
            str(output_path),
            "--summary-output",
            "-",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(output_path.read_text(encoding="utf-8")) if output_path.is_file() else {}
    return completed.returncode, report, completed.stdout + completed.stderr


class InternalLaunchGateScriptTests(unittest.TestCase):
    def test_ready_when_external_hold_is_only_trial_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _create_repo_fixture(root)

            returncode, report, output = _run_gate(root)

            self.assertEqual(returncode, 0, output)
            self.assertEqual(report.get("decision"), "READY_FOR_INTERNAL_DOGFOOD")
            self.assertEqual(report.get("external_launch_decision"), "HOLD")
            self.assertTrue(report.get("internal_dogfood_only"))
            self.assertEqual(report.get("failed_checks"), [])

    def test_workflow_missing_script_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _create_repo_fixture(root, workflow_script="scripts/run_ci.py")

            returncode, report, output = _run_gate(root)

            self.assertEqual(returncode, 0, output)
            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("ci_entrypoint_available", report.get("failed_checks", []))

    def test_missing_ci_result_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _create_repo_fixture(root)

            returncode, report, output = _run_gate_without_ci_result(root)

            self.assertEqual(returncode, 0, output)
            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("ci_baseline_passed", report.get("failed_checks", []))

    def test_external_security_blocker_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _create_repo_fixture(
                root,
                launch_failed_checks=["trial_loop_volume_and_modality_coverage", "security_gate_evidence"],
            )

            returncode, report, output = _run_gate(root)

            self.assertEqual(returncode, 0, output)
            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("official_launch_gate_accounted", report.get("failed_checks", []))

    def test_api_health_unavailable_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _create_repo_fixture(root, health_status="unavailable", health_http_status=500)

            returncode, report, output = _run_gate(root)

            self.assertEqual(returncode, 0, output)
            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("api_health_ready", report.get("failed_checks", []))

    def test_fixture_evidence_without_internal_label_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _create_repo_fixture(root)

            returncode, report, output = _run_gate(root, "--no-allow-fixture-evidence")

            self.assertEqual(returncode, 0, output)
            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("internal_only_label_present", report.get("failed_checks", []))

    def test_fail_on_hold_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _create_repo_fixture(root, workflow_script="scripts/run_ci.py")

            returncode, report, _output = _run_gate(root, "--fail-on-hold")

            self.assertEqual(returncode, 1)
            self.assertEqual(report.get("decision"), "HOLD")


if __name__ == "__main__":
    unittest.main()
