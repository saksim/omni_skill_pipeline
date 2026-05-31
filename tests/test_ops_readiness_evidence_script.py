from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "ops_evidence.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _release_gate_report() -> dict[str, object]:
    return {
        "generated_at_utc": "2026-05-25T00:00:00+00:00",
        "stage_count": 3,
        "stages": [
            {
                "name": "beta_gate",
                "command": ["python3", "scripts/linux_validate.py", "--stages", "ci"],
            },
            {
                "name": "ga_gate",
                "command": ["python3", "scripts/linux_validate.py", "--stages", "postgres_ga"],
            },
            {
                "name": "roadmap_gate",
                "command": ["python3", "scripts/linux_validate.py", "--stages", "roadmap_extension"],
            },
        ],
    }


def _launch_readiness_report() -> dict[str, object]:
    return {
        "schema_version": "broad_launch_readiness.v1",
        "decision": "HOLD",
        "checks": [
            {"id": "release_switch_go", "status": "pass"},
            {"id": "no_dry_run_relaxed_or_skipped_evidence", "status": "pass"},
        ],
    }


def _doc_sync_report() -> dict[str, object]:
    return {
        "generated_at_utc": "2026-05-25T00:00:00+00:00",
        "status": "pass",
        "failed_count": 0,
    }


def _production_ops_runbook() -> str:
    return """# Production Operations Baseline

## Deploy Workflow
python scripts/release_gate.py
docker run --rm -d

## Validation Workflow
python scripts/launch_gate.py
python scripts/doc_sync.py --output
python scripts/ops_evidence.py

## Rollback Workflow
docker logs

## Backup Workflow
backup

## Restore Workflow
restore

## Incident Response Workflow
incident

## Log Inspection Workflow
docker logs

## Alert Workflow
alert

## Evidence Collection Workflow
evidence
"""


class OpsReadinessEvidenceScriptTests(unittest.TestCase):
    def test_script_generates_pass_report_for_complete_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            release_gate = root / "release-gate.json"
            launch_readiness = root / "launch-readiness.json"
            doc_sync = root / "doc-sync.json"
            launch_beta = root / "launch-beta.md"
            docker_zero = root / "docker-zero-to-release.md"
            production_ops = root / "production-ops.md"
            output = root / "ops-readiness.json"

            _write_json(release_gate, _release_gate_report())
            _write_json(launch_readiness, _launch_readiness_report())
            _write_json(doc_sync, _doc_sync_report())
            launch_beta.write_text("# launch beta\n", encoding="utf-8")
            docker_zero.write_text("# docker zero\n", encoding="utf-8")
            production_ops.write_text(_production_ops_runbook(), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--release-gate-report",
                    str(release_gate),
                    "--launch-readiness-report",
                    str(launch_readiness),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--launch-beta-runbook",
                    str(launch_beta),
                    "--docker-zero-to-release-runbook",
                    str(docker_zero),
                    "--production-ops-runbook",
                    str(production_ops),
                    "--summary-output",
                    "-",
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Operations readiness status=pass", completed.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report.get("overall_status"), "pass")
            self.assertEqual(report.get("failed_checks"), [])

    def test_script_holds_when_production_ops_runbook_missing_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            release_gate = root / "release-gate.json"
            launch_readiness = root / "launch-readiness.json"
            doc_sync = root / "doc-sync.json"
            launch_beta = root / "launch-beta.md"
            docker_zero = root / "docker-zero-to-release.md"
            production_ops = root / "production-ops.md"

            _write_json(release_gate, _release_gate_report())
            _write_json(launch_readiness, _launch_readiness_report())
            _write_json(doc_sync, _doc_sync_report())
            launch_beta.write_text("# launch beta\n", encoding="utf-8")
            docker_zero.write_text("# docker zero\n", encoding="utf-8")
            production_ops.write_text("# incomplete\n\n## Deploy Workflow\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--release-gate-report",
                    str(release_gate),
                    "--launch-readiness-report",
                    str(launch_readiness),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--launch-beta-runbook",
                    str(launch_beta),
                    "--docker-zero-to-release-runbook",
                    str(docker_zero),
                    "--production-ops-runbook",
                    str(production_ops),
                    "--summary-output",
                    "-",
                    "--output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("production_ops_runbook_contract", completed.stdout)
            self.assertIn("Operations readiness status=fail", completed.stdout)


if __name__ == "__main__":
    unittest.main()
