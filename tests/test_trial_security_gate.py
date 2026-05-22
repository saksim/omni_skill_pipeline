from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.validation import evaluate_trial_security


class TrialSecurityGateTests(unittest.TestCase):
    def test_gate_passes_for_sanitized_payload(self) -> None:
        markdown = '\n'.join(
            [
                '---',
                'name: "safe-skill"',
                'description: "Use when the user asks to triage reviewed trial outputs safely."',
                '---',
                '',
                '# Safe Skill',
                '',
                '## Workflow',
                '1. Collect reviewed evidence.',
                '',
                '## Decision Rules',
                '- Keep reviewer in loop for production-impacting actions.',
                '',
                '## Validation',
                '- Confirm approval marker exists.',
                '',
                '## Failure Modes',
                '- Do not auto-publish before review approval.',
            ]
        ) + '\n'
        report = evaluate_trial_security(
            skill_markdown=markdown,
            references={'evidence.md': '# Evidence\n- source redacted\n'},
            request_payload={'sensitivity': 'internal'},
            package_metadata={'review_status': 'published'},
        )
        self.assertEqual(report.status, 'pass')
        self.assertEqual(report.failure_codes, [])

    def test_gate_rejects_secret_path_dangerous_and_sensitive_class(self) -> None:
        markdown = '\n'.join(
            [
                '---',
                'name: "unsafe-skill"',
                'description: "Use when unsafe payload is intentionally tested for trial gate."',
                '---',
                '',
                '# Unsafe Skill',
                '',
                '## Workflow',
                '1. Read C:\\Users\\alice\\secrets.txt then proceed.',
                '',
                '## Decision Rules',
                '- authorization: Bearer sk-live-1234567890abcdefghijklmnop',
                '',
                '## Validation',
                '- Confirm command coverage.',
                '',
                '## Failure Modes',
                '- avoid rm -rf / on production hosts.',
            ]
        ) + '\n'
        report = evaluate_trial_security(
            skill_markdown=markdown,
            request_payload={'sensitivity': 'restricted'},
        )
        self.assertEqual(report.status, 'fail')
        self.assertIn('TRIAL_SECRET_LEAK', report.failure_codes)
        self.assertIn('TRIAL_PRIVATE_LOCAL_ABSOLUTE_PATH', report.failure_codes)
        self.assertIn('TRIAL_DANGEROUS_PRODUCTION_COMMAND', report.failure_codes)
        self.assertIn('TRIAL_UNAPPROVED_SENSITIVE_DATA_CLASS', report.failure_codes)

    def test_gate_accepts_explicitly_approved_sensitive_class(self) -> None:
        markdown = '# Skill\n'
        report = evaluate_trial_security(
            skill_markdown=markdown,
            request_payload={'sensitivity': 'restricted'},
            approved_sensitive_classes={'restricted'},
        )
        self.assertEqual(report.status, 'pass')
        self.assertNotIn('TRIAL_UNAPPROVED_SENSITIVE_DATA_CLASS', report.failure_codes)

    def test_gate_detects_file_uri_as_private_local_path(self) -> None:
        markdown = 'Use file://C:/Users/alice/private-notes.md for debugging only.'
        report = evaluate_trial_security(skill_markdown=markdown)
        self.assertEqual(report.status, 'fail')
        self.assertIn('TRIAL_PRIVATE_LOCAL_ABSOLUTE_PATH', report.failure_codes)

    def test_risk_labels_are_deduplicated(self) -> None:
        markdown = 'authorization: Bearer sk-live-1234567890abcdefghijklmnop\n'
        report = evaluate_trial_security(skill_markdown=markdown)
        risk_codes = [item['code'] for item in report.risk_labels]
        self.assertEqual(risk_codes.count('trial_security_secret_leak_detected'), 1)


if __name__ == '__main__':
    unittest.main()
