from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


class ReleaseConsumerSmokeTests(unittest.TestCase):
    def _write_pack(self, root: Path) -> None:
        source = root / "omni-skill-pipeline-source-test-release.tar.gz"
        wheel = root / "omni_skill_pipeline-0.2.1-py3-none-any.whl"
        coverage = root / "coverage.xml"
        summary = root / "release-summary.md"
        source.write_bytes(b"source")
        wheel.write_bytes(b"wheel")
        coverage.write_text("<coverage />\n", encoding="utf-8")
        summary.write_text("# summary\n", encoding="utf-8")
        manifest = {
            "schema_version": "omni.release_artifacts.v1",
            "release_id": "test-release",
            "project": {
                "name": "omni-skill-pipeline",
                "version": "0.2.1",
            },
            "artifacts": [
                {
                    "path": source.name,
                    "role": "source_archive",
                    "sha256": _sha256(source),
                },
                {
                    "path": wheel.name,
                    "role": "python_wheel",
                    "sha256": _sha256(wheel),
                },
                {
                    "path": coverage.name,
                    "role": "coverage_xml",
                    "sha256": _sha256(coverage),
                },
            ],
        }
        manifest_path = root / "release-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        rows = []
        for path in [coverage, source, wheel, manifest_path, summary]:
            rows.append("%s  %s" % (_sha256(path), path.name))
        (root / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")

    def test_pack_contract_passes_without_install_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            release_dir = Path(tmp_dir)
            report_path = release_dir / "report.json"
            summary_path = release_dir / "summary.md"
            self._write_pack(release_dir)

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/release_consumer_smoke.py",
                    "--release-dir",
                    str(release_dir),
                    "--expected-release-id",
                    "test-release",
                    "--install-mode",
                    "none",
                    "--output",
                    str(report_path),
                    "--summary-output",
                    str(summary_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], "release_consumer_smoke.v1")
            self.assertEqual(report["decision"], "PASS")
            self.assertEqual(report["release"]["project_version"], "0.2.1")
            self.assertIn("Decision: `PASS`", summary_path.read_text(encoding="utf-8"))

    def test_checksum_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            release_dir = Path(tmp_dir)
            self._write_pack(release_dir)
            (release_dir / "coverage.xml").write_text("changed\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/release_consumer_smoke.py",
                    "--release-dir",
                    str(release_dir),
                    "--install-mode",
                    "none",
                    "--print-json",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("sha256_mismatch", completed.stdout)


if __name__ == "__main__":
    unittest.main()
