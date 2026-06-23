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

from omni_skill_pipeline.exporters import AgentSkillExporter
from omni_skill_pipeline.models import AgentSkillTarget
from omni_skill_pipeline.validation import validate_skill_package


class AgentSkillExporterSecurityGateTests(unittest.TestCase):
    def test_exporter_blocks_unsafe_bundle_before_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_bundle(root, unsafe=True)
            exporter = AgentSkillExporter(output_root=root / 'out')

            with self.assertRaisesRegex(ValueError, 'Trial security gate failed before export'):
                exporter.export_from_bundle(bundle_path=bundle_path, target=AgentSkillTarget.PORTABLE)

            self.assertFalse((root / 'out').exists())

    def test_exporter_uses_per_evidence_source_uri_for_corpus_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_bundle(root, unsafe=False, with_corpus=True)
            exporter = AgentSkillExporter(output_root=root / 'out')

            results = exporter.export_from_bundle(bundle_path=bundle_path, target=AgentSkillTarget.PORTABLE)
            self.assertEqual(len(results), 1)
            package = json.loads(results[0].package_path.read_text(encoding='utf-8'))
            refs = package.get('references', [])
            self.assertEqual(len(refs), 2)
            first = refs[0]
            second = refs[1]
            self.assertIn('incident-a.md', first.get('source_uri', ''))
            self.assertIn('incident-b.md', second.get('source_uri', ''))

    def test_exporter_uses_published_review_task_for_stale_draft_bundle_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_bundle(root, unsafe=False, review_status='draft', auto_publish=True)
            exporter = AgentSkillExporter(output_root=root / 'out')

            results = exporter.export_from_bundle(bundle_path=bundle_path, target=AgentSkillTarget.PORTABLE)

            package = json.loads(results[0].package_path.read_text(encoding='utf-8'))
            self.assertEqual(package['review_status'], 'published')
            self.assertEqual(package['metadata']['review_status_source'], 'review_task')
            self.assertEqual(package['metadata']['review_task_id'], 'review-task-1')
            report = validate_skill_package(package_path=results[0].package_path.parent, max_lines=500)
            self.assertEqual(report.status, 'pass')

    def _write_bundle(
        self,
        root: Path,
        *,
        unsafe: bool,
        with_corpus: bool = False,
        review_status: str = 'published',
        auto_publish: bool = False,
    ) -> Path:
        bundle_dir = root / 'bundle'
        publication_dir = bundle_dir / 'publications'
        references_dir = publication_dir / 'references'
        references_dir.mkdir(parents=True, exist_ok=True)
        markdown = '\n'.join(
            [
                '---',
                'name: "sample-skill"',
                'description: "Use when the user asks to run reviewed controlled trial workflow safely."',
                '---',
                '',
                '# Sample Skill',
                '',
                '## Workflow',
                '1. %s' % ('Read C:\\Users\\alice\\secrets.txt first.' if unsafe else 'Collect reviewed evidence first.'),
                '',
                '## Decision Rules',
                ('- authorization: Bearer sk-live-1234567890abcdefghijklmnop' if unsafe else '- Keep manual review.'),
                '',
                '## Validation',
                '- Confirm package pass.',
                '',
                '## Failure Modes',
                '- Do not auto publish without approval.',
            ]
        ) + '\n'
        (publication_dir / 'SKILL.md').write_text(markdown, encoding='utf-8')
        (references_dir / 'evidence.md').write_text('# Evidence\n', encoding='utf-8')
        (references_dir / 'examples.md').write_text('# Examples\n', encoding='utf-8')

        payload: dict[str, object] = {
            'skill': {
                'name': 'sample-skill',
                'summary': 'sample description',
                'skill_id': 'skill-1',
                'review_status': review_status,
            },
            'asset': {'source_uri': 'file:///tmp/default.md'},
            'evidence_units': [
                {'evidence_id': 'ev-1', 'asset_id': 'asset-1', 'span_ref': 'line:1'},
                {'evidence_id': 'ev-2', 'asset_id': 'asset-2', 'span_ref': 'line:2'},
            ],
            'artifacts': {
                'publication_skill_markdown': str(publication_dir / 'SKILL.md'),
                'publication_manifest': str(publication_dir / 'manifest.json'),
            },
            'request_payload': {'sensitivity': 'internal' if not unsafe else 'restricted'},
            'adapter_metadata': {'reviewer_packet': {'review_task_id': 'review-task-1'}},
        }
        if auto_publish:
            payload['adapter_metadata']['review_task'] = {
                'review_task_id': 'review-task-1',
                'decision': 'auto_publish',
                'status': 'published',
            }
        if with_corpus:
            payload['corpus_assets'] = [
                {'asset_id': 'asset-1', 'source_uri': 'file:///fixtures/incident-a.md'},
                {'asset_id': 'asset-2', 'source_uri': 'file:///fixtures/incident-b.md'},
            ]

        bundle_path = bundle_dir / 'bundle.json'
        bundle_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return bundle_path


if __name__ == '__main__':
    unittest.main()
