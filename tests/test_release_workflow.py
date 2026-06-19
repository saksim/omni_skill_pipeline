from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"


class ReleaseWorkflowTests(unittest.TestCase):
    def test_release_workflow_exists_and_has_expected_triggers(self) -> None:
        content = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("name: Release", content)
        self.assertIn("branches:", content)
        self.assertIn("- main", content)
        self.assertIn("tags:", content)
        self.assertIn('- "v*"', content)
        self.assertIn("workflow_dispatch:", content)
        self.assertIn("publish_github_release:", content)
        self.assertIn("release_tag:", content)

    def test_release_workflow_builds_verifiable_artifact_pack(self) -> None:
        content = WORKFLOW_PATH.read_text(encoding="utf-8")

        required_markers = [
            "permissions:",
            "contents: write",
            "fetch-depth: 0",
            "python-version: \"3.11\"",
            "python -m pip install -r requirements-dev.txt",
            "python -m pip check",
            "python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml",
            "python -m pip wheel . --no-deps --wheel-dir dist",
            "python scripts/release_artifacts.py",
            "--coverage-xml coverage.xml",
            "actions/upload-artifact@v4",
            "if-no-files-found: error",
        ]
        for marker in required_markers:
            self.assertIn(marker, content, "Missing workflow marker: %s" % marker)

    def test_release_workflow_only_publishes_github_release_for_tags_or_manual_publish(self) -> None:
        content = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("Publish GitHub Release", content)
        self.assertIn(
            "github.ref_type == 'tag' || (github.event_name == 'workflow_dispatch' && inputs.publish_github_release == true)",
            content,
        )
        self.assertIn("release_tag is required for manual GitHub Release publication.", content)
        self.assertIn("git tag \"${RELEASE_TAG}\" \"${GITHUB_SHA}\"", content)
        self.assertIn("gh release create \"${RELEASE_TAG}\"", content)
        self.assertIn("--notes-file \"release-artifacts/${RELEASE_ID}/release-summary.md\"", content)


if __name__ == "__main__":
    unittest.main()
