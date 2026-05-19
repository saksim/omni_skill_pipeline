from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.config import load_settings
from omni_skill_pipeline.providers.openai_provider import OpenAIClientMixin


class OpenAIProviderConfigTests(unittest.TestCase):
    def test_load_settings_reads_openai_timeout_seconds(self) -> None:
        with patch.dict(os.environ, {'OMNI_OPENAI_TIMEOUT_SECONDS': '17.25'}, clear=False):
            settings = load_settings(repo_root=REPO_ROOT)
        self.assertEqual(settings.openai_timeout_seconds, 17.25)

    def test_load_settings_reads_circuit_breaker_and_failure_budget(self) -> None:
        with patch.dict(
            os.environ,
            {
                'OMNI_OPENAI_CIRCUIT_BREAKER_CONSECUTIVE_FAILURES': '4',
                'OMNI_OPENAI_CIRCUIT_BREAKER_COOLDOWN_SECONDS': '45',
                'OMNI_OPENAI_FAILURE_BUDGET_MAX_FAILURES': '9',
                'OMNI_OPENAI_FAILURE_BUDGET_WINDOW_SECONDS': '120',
            },
            clear=False,
        ):
            settings = load_settings(repo_root=REPO_ROOT)
        self.assertEqual(settings.openai_circuit_breaker_consecutive_failures, 4)
        self.assertEqual(settings.openai_circuit_breaker_cooldown_seconds, 45.0)
        self.assertEqual(settings.openai_failure_budget_max_failures, 9)
        self.assertEqual(settings.openai_failure_budget_window_seconds, 120.0)

    def test_load_settings_reads_controlled_trial_review_mode_flags(self) -> None:
        with patch.dict(
            os.environ,
            {
                'OMNI_CONTROLLED_TRIAL_REVIEW_MODE': 'true',
                'OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE': 'trial_gate_manual_review',
            },
            clear=False,
        ):
            settings = load_settings(repo_root=REPO_ROOT)
        self.assertTrue(settings.controlled_trial_review_mode)
        self.assertEqual(settings.controlled_trial_review_reason_code, 'trial_gate_manual_review')

    def test_client_mixin_wires_timeout_to_openai_client(self) -> None:
        captured_kwargs: dict[str, object] = {}

        class _FakeClient(object):
            pass

        def _fake_openai_client(**kwargs):
            captured_kwargs.update(kwargs)
            return _FakeClient()

        settings = SimpleNamespace(
            openai_api_key='test-key',
            openai_base_url='https://example.invalid/v1',
            openai_timeout_seconds=33.0,
            openai_retry_max_attempts=3,
            openai_retry_base_delay_seconds=0.5,
            openai_circuit_breaker_consecutive_failures=3,
            openai_circuit_breaker_cooldown_seconds=30.0,
            openai_failure_budget_max_failures=6,
            openai_failure_budget_window_seconds=60.0,
        )

        with patch('omni_skill_pipeline.providers.openai_provider.OpenAI', side_effect=_fake_openai_client):
            mixin = OpenAIClientMixin(settings)

        self.assertIsInstance(mixin.client, _FakeClient)
        self.assertEqual(mixin.request_timeout, 33.0)
        self.assertEqual(mixin.retry_max_attempts, 3)
        self.assertEqual(mixin.retry_base_delay_seconds, 0.5)
        self.assertEqual(mixin.circuit_breaker_consecutive_failures, 3)
        self.assertEqual(mixin.circuit_breaker_cooldown_seconds, 30.0)
        self.assertEqual(mixin.failure_budget_max_failures, 6)
        self.assertEqual(mixin.failure_budget_window_seconds, 60.0)
        self.assertEqual(captured_kwargs['api_key'], 'test-key')
        self.assertEqual(captured_kwargs['base_url'], 'https://example.invalid/v1')
        self.assertEqual(captured_kwargs['timeout'], 33.0)


if __name__ == '__main__':
    unittest.main()
