from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "tune_review.py"
MANIFEST_PATH = REPO_ROOT / "docs" / "current" / "status" / "baselines" / "e7-calibration-manifest.json"


class TuneReviewPolicyScriptTests(unittest.TestCase):
    def test_script_smoke_generates_calibration_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "calibration-report.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--manifest",
                    str(MANIFEST_PATH),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Calibration samples=", completed.stdout)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(int(payload.get("sample_count", 0)), 1)
            self.assertIn("agreement", payload)
            self.assertIn("thresholds", payload)
            self.assertIn("suggested", payload["thresholds"])

    def test_script_rejects_invalid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_manifest = Path(tmp_dir) / "bad-manifest.json"
            bad_manifest.write_text(json.dumps({"samples": []}, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--manifest",
                    str(bad_manifest),
                    "--output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("Calibration failed:", completed.stderr)


if __name__ == "__main__":
    unittest.main()
