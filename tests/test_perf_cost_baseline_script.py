from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'perf_baseline.py'


def _manifest_payload() -> dict[str, object]:
    return {
        'manifest_id': 'e11-perf-cost-baseline-test',
        'manifest_version': '1.0',
        'samples': [
            {
                'sample_id': 'S-TEXT-01',
                'modality': 'text',
                'baseline_metrics': {
                    'duration_ms': 120.0,
                    'token_usage': {
                        'input_tokens': 240,
                        'output_tokens': 80,
                        'total_tokens': 320,
                    },
                    'provider_calls': {
                        'text_adapter': 1,
                        'publication_orchestrator': 1,
                    },
                },
                'thresholds': {
                    'max_duration_increase_ratio': 0.2,
                    'max_token_increase_ratio': 0.15,
                    'max_provider_call_increase': 1,
                },
            },
            {
                'sample_id': 'S-VIDEO-01',
                'modality': 'video',
                'baseline_metrics': {
                    'duration_ms': 800.0,
                    'token_usage': {
                        'input_tokens': 1200,
                        'output_tokens': 240,
                        'total_tokens': 1440,
                    },
                    'provider_calls': {
                        'media_processor': 1,
                        'transcriber': 1,
                        'ocr_provider': 1,
                        'publication_orchestrator': 1,
                    },
                },
                'thresholds': {
                    'max_duration_increase_ratio': 0.25,
                    'max_token_increase_ratio': 0.2,
                    'max_provider_call_increase': 2,
                },
            },
        ],
    }


class PerfCostBaselineScriptTests(unittest.TestCase):
    def test_script_smoke_compares_duration_token_and_provider_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / 'manifest.json'
            candidate_path = tmp_path / 'candidate.json'
            output_path = tmp_path / 'perf-cost-baseline-report.json'
            manifest_path.write_text(json.dumps(_manifest_payload(), ensure_ascii=False, indent=2), encoding='utf-8')
            candidate_path.write_text(
                json.dumps(
                    {
                        'samples': [
                            {
                                'sample_id': 'S-TEXT-01',
                                'duration_ms': 132.0,
                                'token_usage': {
                                    'input_tokens': 250,
                                    'output_tokens': 82,
                                    'total_tokens': 332,
                                },
                                'provider_calls': {
                                    'text_adapter': 1,
                                    'publication_orchestrator': 1,
                                },
                            },
                            {
                                'sample_id': 'S-VIDEO-01',
                                'duration_ms': 860.0,
                                'token_usage': {
                                    'input_tokens': 1220,
                                    'output_tokens': 250,
                                    'total_tokens': 1470,
                                },
                                'provider_calls': {
                                    'media_processor': 1,
                                    'transcriber': 1,
                                    'ocr_provider': 1,
                                    'publication_orchestrator': 1,
                                },
                            },
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--manifest',
                    str(manifest_path),
                    '--candidate',
                    str(candidate_path),
                    '--output',
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Perf-cost baseline samples=2', completed.stdout)
            self.assertIn('Regressed samples: none', completed.stdout)
            payload = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(payload.get('sample_count'), 2)
            self.assertEqual(payload.get('regressed_count'), 0)
            self.assertEqual(
                payload.get('compared_metrics'),
                ['duration_ms', 'token_usage.total_tokens', 'provider_calls_total'],
            )

    def test_script_fail_on_regression_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / 'manifest.json'
            candidate_path = tmp_path / 'candidate.json'
            manifest_path.write_text(json.dumps(_manifest_payload(), ensure_ascii=False, indent=2), encoding='utf-8')
            candidate_path.write_text(
                json.dumps(
                    {
                        'samples': [
                            {
                                'sample_id': 'S-TEXT-01',
                                'duration_ms': 180.0,
                                'token_usage': {
                                    'input_tokens': 330,
                                    'output_tokens': 100,
                                    'total_tokens': 430,
                                },
                                'provider_calls': {
                                    'text_adapter': 1,
                                    'publication_orchestrator': 2,
                                },
                            },
                            {
                                'sample_id': 'S-VIDEO-01',
                                'duration_ms': 860.0,
                                'token_usage': {
                                    'input_tokens': 1220,
                                    'output_tokens': 250,
                                    'total_tokens': 1470,
                                },
                                'provider_calls': {
                                    'media_processor': 1,
                                    'transcriber': 1,
                                    'ocr_provider': 1,
                                    'publication_orchestrator': 1,
                                },
                            },
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--manifest',
                    str(manifest_path),
                    '--candidate',
                    str(candidate_path),
                    '--output',
                    '-',
                    '--fail-on-regression',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn('Regressed samples: S-TEXT-01', completed.stdout)


if __name__ == '__main__':
    unittest.main()
