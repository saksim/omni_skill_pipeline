from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _workflow_content() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _job_body(content: str, job_name: str) -> str:
    marker = "\n  %s:\n" % job_name
    start = content.find(marker)
    if start == -1:
        return ""
    body = content[start + len(marker) :]
    next_job = re.search(r"\n  [A-Za-z0-9_-]+:\n", body)
    if next_job:
        return body[: next_job.start()]
    return body


class CiWorkflowTests(unittest.TestCase):
    def test_ci_workflow_runs_supported_python_matrix(self) -> None:
        content = _workflow_content()

        required_markers = [
            "name: CI",
            'python-version: ["3.11", "3.12"]',
            "python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml",
            "name: ci-evidence-py${{ matrix.python-version }}",
        ]
        for marker in required_markers:
            self.assertIn(marker, content, "Missing CI workflow marker: %s" % marker)

    def test_ci_workflow_archives_ci_evidence_contract(self) -> None:
        content = _workflow_content()

        required_markers = [
            "ci-evidence-contract:",
            "python scripts/doc_sync.py --output ci-evidence/doc_sync.json",
            "python scripts/release_artifacts.py",
            "python scripts/release_consumer_smoke.py",
            "python scripts/launch_gate.py",
            "python scripts/ci_evidence.py",
            "name: ci-evidence-contract",
        ]
        for marker in required_markers:
            self.assertIn(marker, content, "Missing CI evidence marker: %s" % marker)

    def test_ci_workflow_runs_real_docker_smoke_job(self) -> None:
        content = _workflow_content()
        docker_job = _job_body(content, "docker-smoke")
        self.assertTrue(docker_job, "Missing docker-smoke job")

        required_markers = [
            "needs: test",
            "DOCKER_SMOKE_DIR: docker-smoke",
            "Run Docker container smoke",
            "python scripts/container_smoke.py",
            '--image-tag "omni-skill-pipeline:ci-${short_sha}"',
            '--container-name "omni-ci-smoke-${short_sha}"',
            "--port 18000",
            "--timeout-seconds 60",
            '--docker-config-dir "${RUNNER_TEMP}/docker-config"',
            '--output "${DOCKER_SMOKE_DIR}/container_smoke_report.json"',
            '--summary-output "${DOCKER_SMOKE_DIR}/container_smoke_summary.md"',
            "--print-json",
            "Upload Docker smoke evidence",
            "name: docker-smoke-evidence",
        ]
        for marker in required_markers:
            self.assertIn(marker, docker_job, "Missing Docker smoke marker: %s" % marker)

        self.assertNotIn("--dry-run", docker_job)
        self.assertNotIn("--skip-build", docker_job)
        self.assertNotIn("--skip-run", docker_job)

    def test_ci_evidence_contract_requires_docker_smoke_success(self) -> None:
        content = _workflow_content()
        evidence_job = _job_body(content, "ci-evidence-contract")
        self.assertTrue(evidence_job, "Missing ci-evidence-contract job")

        required_markers = [
            "- docker-smoke",
            "needs.docker-smoke.result != 'success'",
            "Docker smoke did not pass",
            "needs.docker-smoke.result == 'success'",
        ]
        for marker in required_markers:
            self.assertIn(marker, evidence_job, "Missing Docker gate marker: %s" % marker)


if __name__ == "__main__":
    unittest.main()
