from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_provider_ga_validation.py'


class ProviderGaValidationScriptTests(unittest.TestCase):
    def test_script_dry_run_emits_default_provider_ga_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'provider-ga-plan.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--dry-run',
                    '--output',
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(
                'Selected stages: provider_retry, provider_circuit_breaker, provider_failure_budget, provider_config_contract, provider_call_audit, provider_footprint',
                completed.stdout,
            )
            self.assertIn('tests.test_openai_provider_retry.OpenAIProviderRetryTests.test_transcribe_retries_on_transient_failure', completed.stdout)
            self.assertIn('tests.test_openai_provider_retry.OpenAIProviderRetryTests.test_failure_storm_opens_circuit_breaker_and_fast_fails', completed.stdout)
            self.assertIn('tests.test_openai_provider_retry.OpenAIProviderRetryTests.test_failure_budget_opens_circuit_even_without_consecutive_threshold', completed.stdout)
            self.assertIn('tests.test_openai_provider_config.OpenAIProviderConfigTests', completed.stdout)
            self.assertIn('tests.test_provider_audit_tp_e12.ProviderAuditTpE12Tests.test_openai_mixin_emits_provider_call_audit_snapshot', completed.stdout)
            self.assertIn('tests.test_provider_audit_tp_e12.ProviderAuditTpE12Tests.test_service_distill_corpus_emits_provider_footprint', completed.stdout)

            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('stage_count'), 6)
            self.assertEqual(
                [item.get('name') for item in report.get('stages', [])],
                [
                    'provider_retry',
                    'provider_circuit_breaker',
                    'provider_failure_budget',
                    'provider_config_contract',
                    'provider_call_audit',
                    'provider_footprint',
                ],
            )

    def test_script_respects_stage_selection(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'provider_circuit_breaker',
                'provider_call_audit',
                '--dry-run',
                '--output',
                '-',
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('Selected stages: provider_circuit_breaker, provider_call_audit', completed.stdout)
        self.assertIn('tests.test_openai_provider_retry.OpenAIProviderRetryTests.test_failure_storm_opens_circuit_breaker_and_fast_fails', completed.stdout)
        self.assertIn('tests.test_provider_audit_tp_e12.ProviderAuditTpE12Tests.test_openai_mixin_emits_provider_call_audit_snapshot', completed.stdout)
        self.assertNotIn('tests.test_openai_provider_retry.OpenAIProviderRetryTests.test_transcribe_retries_on_transient_failure', completed.stdout)
        self.assertNotIn('tests.test_openai_provider_retry.OpenAIProviderRetryTests.test_failure_budget_opens_circuit_even_without_consecutive_threshold', completed.stdout)
        self.assertNotIn('tests.test_openai_provider_config.OpenAIProviderConfigTests', completed.stdout)
        self.assertNotIn('tests.test_provider_audit_tp_e12.ProviderAuditTpE12Tests.test_service_distill_corpus_emits_provider_footprint', completed.stdout)


if __name__ == '__main__':
    unittest.main()
