from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "ci_evidence.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_ready_pack(evidence_dir: Path, *, launch_decision: str = "HOLD") -> None:
    for version in ("3.11", "3.12"):
        tag = version.replace(".", "_")
        coverage_name = "coverage-python-%s.xml" % version
        (evidence_dir / coverage_name).write_text(
            '<?xml version="1.0" ?><coverage version="7.0" line-rate="0.5"></coverage>\n',
            encoding="utf-8",
        )
        _write_json(
            evidence_dir / ("ci_summary_python_%s.json" % tag),
            {
                "schema_version": "ci_summary.v1",
                "generated_at_utc": "2026-06-23T00:00:00Z",
                "declared_python_version": version,
                "python_version": "%s.9" % version,
                "status": "passed",
                "exit_code": 0,
                "commands": [
                    {
                        "name": "repo_ci",
                        "command": (
                            "python scripts/ci.py --isolate-test-files "
                            "--coverage-fail-under 50 --coverage-xml coverage.xml"
                        ),
                        "exit_code": 0,
                    }
                ],
                "coverage_xml": coverage_name,
            },
        )

    (evidence_dir / "coverage.xml").write_text(
        '<?xml version="1.0" ?><coverage version="7.0" line-rate="0.5"></coverage>\n',
        encoding="utf-8",
    )
    _write_json(
        evidence_dir / "doc_sync.json",
        {
            "status": "pass",
            "failed_count": 0,
            "check_count": 1,
            "checks": [{"name": "script_name_map_coverage", "status": "pass"}],
        },
    )
    _write_json(
        evidence_dir / "release_artifacts.json",
        {
            "schema_version": "omni.release_artifacts.v1",
            "release_id": "ci-evidence-test",
            "source_archive": {
                "source_archive_mode": "git_archive",
                "source_archive_sha256": "a" * 64,
            },
            "artifacts": [
                {"path": "source.tar.gz", "role": "source_archive", "sha256": "a" * 64},
                {"path": "pkg.whl", "role": "python_wheel", "sha256": "b" * 64},
            ],
        },
    )
    _write_json(
        evidence_dir / "release_consumer_smoke.json",
        {
            "schema_version": "release_consumer_smoke.v1",
            "decision": "PASS",
            "stages": [{"name": "manifest", "status": "pass"}],
        },
    )
    _write_json(
        evidence_dir / "launch_gate.json",
        {
            "schema_version": "broad_launch_readiness.v1",
            "decision": launch_decision,
            "check_count": 1,
            "failed_checks": ["trial_loop_volume_and_modality_coverage"],
            "checks": [{"id": "trial_loop_volume_and_modality_coverage", "status": "fail"}],
        },
    )


def _run_ci_evidence(evidence_dir: Path, output_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--evidence-dir",
            str(evidence_dir),
            "--output",
            str(output_path),
            "--summary-output",
            str(output_path.with_suffix(".md")),
            "--fail-on-blocked",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


class CiEvidenceScriptTests(unittest.TestCase):
    def test_ready_pack_accepts_hold_launch_gate_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_dir = Path(temp_dir)
            _write_ready_pack(evidence_dir, launch_decision="HOLD")
            output_path = evidence_dir / "report.json"

            completed = _run_ci_evidence(evidence_dir, output_path)

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "CI_EVIDENCE_READY")
            self.assertEqual(report["blocking_codes"], [])
            launch_check = next(check for check in report["checks"] if check["id"] == "launch_gate")
            self.assertTrue(launch_check["details"]["hold_is_allowed"])

    def test_missing_python_summary_blocks_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_dir = Path(temp_dir)
            _write_ready_pack(evidence_dir)
            (evidence_dir / "ci_summary_python_3_12.json").unlink()
            output_path = evidence_dir / "report.json"

            completed = _run_ci_evidence(evidence_dir, output_path)

            self.assertEqual(completed.returncode, 1)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "CI_EVIDENCE_BLOCKED")
            self.assertIn("ci_summary_missing:3.12", report["blocking_codes"])

    def test_failed_doc_sync_blocks_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_dir = Path(temp_dir)
            _write_ready_pack(evidence_dir)
            _write_json(
                evidence_dir / "doc_sync.json",
                {
                    "status": "fail",
                    "failed_count": 1,
                    "checks": [{"name": "script_name_map_coverage", "status": "fail"}],
                },
            )
            output_path = evidence_dir / "report.json"

            completed = _run_ci_evidence(evidence_dir, output_path)

            self.assertEqual(completed.returncode, 1)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("doc_sync_status_failed", report["blocking_codes"])
            self.assertIn("doc_sync_failed_count_nonzero", report["blocking_codes"])

    def test_failed_release_consumer_smoke_blocks_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_dir = Path(temp_dir)
            _write_ready_pack(evidence_dir)
            _write_json(
                evidence_dir / "release_consumer_smoke.json",
                {
                    "schema_version": "release_consumer_smoke.v1",
                    "decision": "FAIL",
                    "stages": [{"name": "manifest", "status": "fail"}],
                },
            )
            output_path = evidence_dir / "report.json"

            completed = _run_ci_evidence(evidence_dir, output_path)

            self.assertEqual(completed.returncode, 1)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("release_consumer_smoke_decision_not_pass", report["blocking_codes"])


if __name__ == "__main__":
    unittest.main()
