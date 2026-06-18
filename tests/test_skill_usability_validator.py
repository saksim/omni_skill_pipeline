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

from omni_skill_pipeline.validation import validate_skill_package


class SkillUsabilityValidatorTests(unittest.TestCase):
    def test_validator_passes_for_review_approved_safe_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = self._write_valid_package(root)
            report = validate_skill_package(package_path=package_dir, max_lines=500)

        self.assertEqual(report.status, 'pass')
        self.assertEqual(report.failure_codes, [])

    def test_validator_catches_missing_frontmatter_and_review_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = self._write_valid_package(root)
            (package_dir / 'SKILL.md').write_text(
                '# Missing Frontmatter\n\n## Workflow\n1. do x\n',
                encoding='utf-8',
            )
            report = validate_skill_package(package_path=package_dir, max_lines=500)

        self.assertEqual(report.status, 'fail')
        self.assertIn('MISSING_FRONTMATTER', report.failure_codes)
        self.assertIn('MISSING_SECTION', report.failure_codes)

    def test_validator_catches_path_secret_and_dangerous_command_leaks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = self._write_valid_package(root)
            (package_dir / 'SKILL.md').write_text(
                '\n'.join(
                    [
                        '---',
                        'name: "db-skill"',
                        'description: "Use when the user asks to inspect slow SQL and produce safe changes."',
                        '---',
                        '',
                        '# DB Skill',
                        '',
                        '## Workflow',
                        '1. Read C:\\\\Users\\\\alice\\\\secrets.txt then proceed.',
                        '',
                        '## Decision Rules',
                        '- api_key: sk-live-1234567890abcdefghijklmnop',
                        '',
                        '## Validation',
                        '- Confirm checks pass.',
                        '',
                        '## Failure Modes',
                        '- Never run rm -rf / in production.',
                        '',
                        '## References',
                        '- [Evidence](references/evidence.md)',
                    ]
                )
                + '\n',
                encoding='utf-8',
            )
            report = validate_skill_package(package_path=package_dir, max_lines=500)

        self.assertEqual(report.status, 'fail')
        self.assertIn('ABSOLUTE_PATH_LEAK', report.failure_codes)
        self.assertIn('SECRET_TOKEN_LEAK', report.failure_codes)
        self.assertIn('DANGEROUS_COMMAND_MARKER', report.failure_codes)

    def test_validator_catches_missing_required_sections_and_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = self._write_valid_package(root)
            (package_dir / 'SKILL.md').write_text(
                '\n'.join(
                    [
                        '---',
                        'name: "short-skill"',
                        'description: "Use when the user asks for short action plan in reviewed trial loop."',
                        '---',
                        '',
                        '# Short Skill',
                        '',
                        '## Workflow',
                        '1. collect inputs',
                    ]
                )
                + '\n',
                encoding='utf-8',
            )
            refs = package_dir / 'references'
            for item in refs.rglob('*'):
                if item.is_file():
                    item.unlink()
            report = validate_skill_package(package_path=package_dir, max_lines=500)

        self.assertEqual(report.status, 'fail')
        self.assertIn('MISSING_SECTION', report.failure_codes)
        self.assertIn('EMPTY_REFERENCES_DIR', report.failure_codes)

    def test_validator_catches_weak_description(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = self._write_valid_package(root)
            (package_dir / 'SKILL.md').write_text(
                '\n'.join(
                    [
                        '---',
                        'name: "weak-description"',
                        'description: "General helper."',
                        '---',
                        '',
                        '# Weak Description',
                        '',
                        '## Workflow',
                        '1. collect inputs',
                        '',
                        '## Decision Rules',
                        '- do one thing',
                        '',
                        '## Validation',
                        '- check output',
                        '',
                        '## Failure Modes',
                        '- skip auto publish',
                        '',
                        '## References',
                        '- [Evidence](references/evidence.md)',
                    ]
                )
                + '\n',
                encoding='utf-8',
            )
            report = validate_skill_package(package_path=package_dir, max_lines=500)

        self.assertEqual(report.status, 'fail')
        self.assertIn('WEAK_DESCRIPTION', report.failure_codes)

    def _write_valid_package(self, root: Path) -> Path:
        package_dir = root / 'portable' / 'sample-skill'
        references_dir = package_dir / 'references'
        references_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / 'SKILL.md').write_text(
            '\n'.join(
                [
                    '---',
                    'name: "sample-skill"',
                    (
                        'description: "Use when the user asks to triage an incident, '
                        'validate root cause, and prepare a reviewed remediation plan."'
                    ),
                    '---',
                    '',
                    '# Sample Skill',
                    '',
                    '## Workflow',
                    '1. Collect incident summary and evidence.',
                    '',
                    '## Decision Rules',
                    '- If evidence conflicts, escalate to reviewer.',
                    '',
                    '## Validation',
                    '- Confirm output maps to evidence ids.',
                    '',
                    '## Failure Modes',
                    '- Do not auto-publish before approval.',
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
                    'review_status': 'published',
                    'package_name': 'sample-skill',
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
