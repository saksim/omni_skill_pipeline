from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_skill_usability_validator.py'


class SkillUsabilityValidatorScriptTests(unittest.TestCase):
    def test_script_passes_on_validated_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = self._write_package(root, approved=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--package',
                    str(package_dir),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn('"status": "pass"', completed.stdout)
            self.assertIn('Skill usability validation passed.', completed.stdout)

    def test_script_fails_with_explicit_failure_codes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = self._write_package(root, approved=False)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--package',
                    str(package_dir),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn('"status": "fail"', completed.stdout)
            self.assertIn('REVIEW_APPROVAL_MISSING', completed.stdout)
            self.assertIn('Skill usability validation failed.', completed.stdout)

    def _write_package(self, root: Path, *, approved: bool) -> Path:
        package_dir = root / 'portable' / 'validator-script-skill'
        references_dir = package_dir / 'references'
        references_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / 'SKILL.md').write_text(
            '\n'.join(
                [
                    '---',
                    'name: "validator-script-skill"',
                    (
                        'description: "Use when the user asks to triage an incident, '
                        'validate evidence, and prepare a reviewed remediation plan."'
                    ),
                    '---',
                    '',
                    '# Validator Script Skill',
                    '',
                    '## Workflow',
                    '1. Gather evidence and summarize root cause.',
                    '',
                    '## Decision Rules',
                    '- If confidence is low, request reviewer escalation.',
                    '',
                    '## Validation',
                    '- Confirm mapped evidence IDs are complete.',
                    '',
                    '## Failure Modes',
                    '- Do not auto-publish before review approval.',
                    '',
                    '## References',
                    '- [Evidence](references/evidence.md)',
                ]
            )
            + '\n',
            encoding='utf-8',
        )
        (references_dir / 'evidence.md').write_text('# Evidence\n', encoding='utf-8')
        (package_dir / 'agent_skill_package.json').write_text(
            json.dumps(
                {
                    'review_status': 'published' if approved else 'review_pending',
                    'package_name': 'validator-script-skill',
                },
                ensure_ascii=False,
                indent=2,
            )
            + '\n',
            encoding='utf-8',
        )
        return package_dir


if __name__ == '__main__':
    unittest.main()
