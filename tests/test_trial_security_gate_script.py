from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_trial_security_gate.py'


class TrialSecurityGateScriptTests(unittest.TestCase):
    def test_script_passes_for_safe_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_bundle(root, unsafe=False)
            output_path = root / 'security-report.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--bundle',
                    str(bundle_path),
                    '--output',
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Trial security gate passed.', completed.stdout)
            self.assertTrue(output_path.is_file())
            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('status'), 'pass')

    def test_script_fails_for_unsafe_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_bundle(root, unsafe=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--bundle',
                    str(bundle_path),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn('TRIAL_SECRET_LEAK', completed.stdout)
            self.assertIn('TRIAL_PRIVATE_LOCAL_ABSOLUTE_PATH', completed.stdout)

    def _write_bundle(self, root: Path, *, unsafe: bool) -> Path:
        bundle_dir = root / 'bundle'
        publication_dir = bundle_dir / 'publications'
        references_dir = publication_dir / 'references'
        references_dir.mkdir(parents=True, exist_ok=True)

        markdown = '\n'.join(
            [
                '---',
                'name: "trial-skill"',
                'description: "Use when the user asks to run controlled trial flow with review."',
                '---',
                '',
                '# Trial Skill',
                '',
                '## Workflow',
                (
                    '1. Inspect C:\\Users\\alice\\secrets.txt before running.'
                    if unsafe
                    else '1. Inspect reviewed evidence before running.'
                ),
                '',
                '## Decision Rules',
                ('- authorization: Bearer sk-live-1234567890abcdefghijklmnop' if unsafe else '- Keep review enabled.'),
                '',
                '## Validation',
                '- Confirm risk gate output.',
                '',
                '## Failure Modes',
                '- Do not auto-publish without review approval.',
            ]
        ) + '\n'
        (publication_dir / 'SKILL.md').write_text(markdown, encoding='utf-8')
        (references_dir / 'evidence.md').write_text('# Evidence\n', encoding='utf-8')

        bundle_payload = {
            'artifacts': {
                'publication_skill_markdown': str(publication_dir / 'SKILL.md'),
            },
            'request_payload': {
                'sensitivity': 'restricted' if unsafe else 'internal',
            },
            'adapter_metadata': {
                'reviewer_packet': {'review_task_id': 'review-task-1'},
            },
        }
        bundle_path = bundle_dir / 'bundle.json'
        bundle_path.write_text(json.dumps(bundle_payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return bundle_path


if __name__ == '__main__':
    unittest.main()
