from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = (
    REPO_ROOT / "docs" / "current" / "operations" / "runbooks" / "docker-zero-to-release.md"
)
TEST_DOCKERFILE_PATH = REPO_ROOT / "Dockerfile.test"
TEST_DOCKERIGNORE_PATH = REPO_ROOT / "Dockerfile.test.dockerignore"


class DockerZeroToReleaseRunbookTests(unittest.TestCase):
    def test_runbook_exists(self) -> None:
        self.assertTrue(RUNBOOK_PATH.exists(), "docker-zero-to-release.md is missing")

    def test_runbook_contains_required_sections(self) -> None:
        content = RUNBOOK_PATH.read_text(encoding="utf-8")
        required_headings = [
            "## Host Assumptions",
            "## Python Contract",
            "## Image Build",
            "## Docker-Only Test Gate",
            "## Release Decision",
            "## Deploy",
            "## Acceptance",
            "## Observability",
            "## Rollback",
            "## From Zero Checklist",
        ]
        for heading in required_headings:
            self.assertIn(heading, content, "Missing heading: %s" % heading)

    def test_runbook_is_host_python_free(self) -> None:
        content = RUNBOOK_PATH.read_text(encoding="utf-8")
        required_markers = [
            "不要求 `python`",
            'requires-python = ">=3.11"',
            "python:3.11-slim",
            "docker build -f Dockerfile.test -t omni-skill-pipeline:test .",
            "docker build -t omni-skill-pipeline:beta .",
            "docker exec omni-skill-beta python --version",
        ]
        for marker in required_markers:
            self.assertIn(marker, content, "Missing marker: %s" % marker)

    def test_runbook_documents_keep_going_module_gates(self) -> None:
        content = RUNBOOK_PATH.read_text(encoding="utf-8")
        required_commands = [
            "scripts/run_ci.py --python python3 --keep-going",
            "scripts/run_linux_validation_suite.py --python python3 --keep-going",
            "scripts/run_release_switch_validation.py --python python3 --keep-going",
        ]
        for command in required_commands:
            self.assertIn(command, content, "Missing command: %s" % command)

    def test_test_image_keeps_tests_in_build_context(self) -> None:
        self.assertTrue(TEST_DOCKERFILE_PATH.exists(), "Dockerfile.test is missing")
        self.assertTrue(
            TEST_DOCKERIGNORE_PATH.exists(),
            "Dockerfile.test.dockerignore is missing",
        )

        dockerfile = TEST_DOCKERFILE_PATH.read_text(encoding="utf-8")
        dockerignore = TEST_DOCKERIGNORE_PATH.read_text(encoding="utf-8")

        self.assertIn("FROM python:3.11-slim", dockerfile)
        self.assertIn("COPY Dockerfile Dockerfile.test Dockerfile.test.dockerignore .dockerignore ./", dockerfile)
        self.assertIn("COPY tests ./tests", dockerfile)
        self.assertIn("COPY scripts ./scripts", dockerfile)
        self.assertIn("docker.io", dockerfile)
        self.assertNotIn("tests/", dockerignore)


if __name__ == "__main__":
    unittest.main()
