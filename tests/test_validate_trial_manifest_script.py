from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'validate_manifest.py'


def _valid_manifest_payload() -> dict[str, object]:
    return {
        'manifest_id': 'cbt02-trial-manifest-test',
        'manifest_version': '1.0',
        'samples': [
            {
                'sample_id': 'sample-text-001',
                'modality': 'text',
                'scenario': 'runbook distillation',
                'source_owner': 'ops-team',
                'sensitivity': 'internal',
                'asset_list': [
                    {
                        'asset_id': 'asset-text-001',
                        'asset_type': 'document',
                        'uri': 'fixtures/text/runbook.md',
                    }
                ],
                'review_owner': 'review-team',
                'target_package_format': 'codex',
                'expected_output_type': 'diagnostic_skill',
            }
        ],
    }


class ValidateTrialManifestScriptTests(unittest.TestCase):
    def test_script_passes_on_valid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / 'manifest.json'
            output_path = tmp_path / 'report.json'
            manifest_path.write_text(
                json.dumps(_valid_manifest_payload(), ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--manifest',
                    str(manifest_path),
                    '--output',
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Trial manifest validation passed.', completed.stdout)
            payload = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(payload.get('status'), 'pass')
            self.assertEqual(payload.get('error_count'), 0)

    def test_script_rejects_unsupported_sensitivity_with_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_payload = _valid_manifest_payload()
            samples = manifest_payload['samples']
            assert isinstance(samples, list)
            sample = samples[0]
            assert isinstance(sample, dict)
            sample['sensitivity'] = 'secret'
            manifest_path = tmp_path / 'manifest.json'
            manifest_path.write_text(
                json.dumps(manifest_payload, ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--manifest',
                    str(manifest_path),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn('sensitivity "secret" is unsupported', completed.stderr)
            self.assertIn('Allowed values:', completed.stderr)

    def test_script_rejects_missing_required_fields_with_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_payload = _valid_manifest_payload()
            samples = manifest_payload['samples']
            assert isinstance(samples, list)
            sample = samples[0]
            assert isinstance(sample, dict)
            sample['asset_list'] = []
            sample['review_owner'] = ''
            manifest_path = tmp_path / 'manifest.json'
            manifest_path.write_text(
                json.dumps(manifest_payload, ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--manifest',
                    str(manifest_path),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn('samples[0].review_owner is required', completed.stderr)
            self.assertIn('samples[0].asset_list must be a non-empty list', completed.stderr)


if __name__ == '__main__':
    unittest.main()
