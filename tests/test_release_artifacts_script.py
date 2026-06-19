from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "release_artifacts.py"


class ReleaseArtifactsScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / "tests" / ".tmp_runtime" / uuid4().hex
        self.dist_dir = self.workspace / "dist"
        self.output_dir = self.workspace / "release"
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.dist_dir / "omni_skill_pipeline-0.2.0-py3-none-any.whl").write_bytes(b"wheel-bytes")
        (self.dist_dir / "coverage.xml").write_text("not a distribution\n", encoding="utf-8")
        (self.workspace / "coverage.xml").write_text("<coverage></coverage>\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def _run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_builds_release_pack_with_manifest_summary_and_hashes(self) -> None:
        completed = self._run_script(
            "--release-id",
            "test-release-001",
            "--output-dir",
            str(self.output_dir),
            "--dist-dir",
            str(self.dist_dir),
            "--coverage-xml",
            str(self.workspace / "coverage.xml"),
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        expected_files = {
            "SHA256SUMS",
            "coverage.xml",
            "omni-skill-pipeline-source-test-release-001.tar.gz",
            "omni_skill_pipeline-0.2.0-py3-none-any.whl",
            "release-manifest.json",
            "release-summary.md",
        }
        self.assertEqual({path.name for path in self.output_dir.iterdir() if path.is_file()}, expected_files)

        manifest = json.loads((self.output_dir / "release-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "omni.release_artifacts.v1")
        self.assertEqual(manifest["release_id"], "test-release-001")
        self.assertEqual(manifest["project"]["name"], "omni-skill-pipeline")
        self.assertEqual(manifest["project"]["version"], "0.2.0")
        self.assertTrue(manifest["git"]["commit"])

        roles = {item["role"] for item in manifest["artifacts"]}
        self.assertEqual(roles, {"source_archive", "python_wheel", "coverage_xml"})

        sha_lines = (self.output_dir / "SHA256SUMS").read_text(encoding="utf-8").strip().splitlines()
        self.assertTrue(any(line.endswith("  release-manifest.json") for line in sha_lines))
        self.assertTrue(any(line.endswith("  release-summary.md") for line in sha_lines))

    def test_rejects_release_ids_that_are_not_filesystem_safe(self) -> None:
        completed = self._run_script(
            "--release-id",
            "../bad",
            "--output-dir",
            str(self.output_dir),
            "--dist-dir",
            str(self.dist_dir),
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("release_id may contain only", completed.stderr)


if __name__ == "__main__":
    unittest.main()
