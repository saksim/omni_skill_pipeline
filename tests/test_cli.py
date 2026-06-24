from __future__ import annotations

import importlib
import io
import json
import tempfile
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import CorpusDistillRequest


class _StubBundle(object):
    def __init__(self) -> None:
        self.artifacts = {
            'skill_markdown': 'skills/drafts/demo-corpus/SKILL.md',
            'skill': 'skills/drafts/demo-corpus/skill.json',
            'publication_skill_markdown': 'skills/drafts/demo-corpus/publications/SKILL.md',
            'publication_skill_json': 'skills/drafts/demo-corpus/publications/skill.json',
            'publication_decision_tree_json': 'skills/drafts/demo-corpus/publications/decision_tree.json',
        }
        self.publications = [
            {'publication_type': 'skill_markdown'},
            {'publication_type': 'skill_json'},
            {'publication_type': 'decision_tree_json'},
        ]
        self.adapter_metadata = {
            'publication_types': ['skill_markdown', 'skill_json', 'decision_tree_json'],
            'review_task': {
                'review_task_id': 'review-task-1',
                'decision': 'review_required',
                'status': 'review_pending',
                'reason_codes': ['traceability_low', 'coverage_low'],
            },
        }
        self.review_task = None


class _CapturingService(object):
    def __init__(self) -> None:
        self.corpus_requests: list[CorpusDistillRequest] = []
        self.repository = _StubReviewQueueRepository()

    def distill_corpus(self, request: CorpusDistillRequest) -> _StubBundle:
        self.corpus_requests.append(request)
        return _StubBundle()

    def distill_text(self, request):  # pragma: no cover - not used in this test module
        raise AssertionError('Unexpected distill_text call')

    def distill_audio(self, request):  # pragma: no cover - not used in this test module
        raise AssertionError('Unexpected distill_audio call')

    def distill_image(self, request):  # pragma: no cover - not used in this test module
        raise AssertionError('Unexpected distill_image call')

    def distill_tabular(self, request):  # pragma: no cover - not used in this test module
        raise AssertionError('Unexpected distill_tabular call')

    def distill_video(self, request):  # pragma: no cover - not used in this test module
        raise AssertionError('Unexpected distill_video call')


def _run_cli(argv: list[str], service: _CapturingService) -> tuple[int, str]:
    module = importlib.import_module('omni_skill_pipeline.cli')
    module = importlib.reload(module)
    with patch.object(module, 'build_service', return_value=service):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = module.main(argv)
    return exit_code, stdout.getvalue()


class CliCorpusCommandTests(unittest.TestCase):
    def test_distill_corpus_accepts_multiple_asset_args(self) -> None:
        service = _CapturingService()
        exit_code, output = _run_cli(
            [
                'distill-corpus',
                '--name',
                'beta-corpus',
                '--asset',
                'text=examples/text_note.md',
                '--asset',
                'audio=examples/audio_transcript.srt',
                '--tag',
                'beta',
                '--tag',
                'ops',
                '--domain',
                'operations',
            ],
            service,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn('skills/drafts/demo-corpus/publications/SKILL.md', output)
        self.assertEqual(len(service.corpus_requests), 1)
        request = service.corpus_requests[0]
        self.assertIsInstance(request, CorpusDistillRequest)
        self.assertEqual(request.name, 'beta-corpus')
        self.assertEqual(len(request.assets), 2)
        self.assertEqual(request.assets[0].modality.value, 'text')
        self.assertEqual(request.assets[0].source_uri, 'examples/text_note.md')
        self.assertEqual(request.assets[0].role, 'primary')
        self.assertEqual(request.assets[1].modality.value, 'audio')
        self.assertEqual(request.assets[1].source_uri, 'examples/audio_transcript.srt')
        self.assertEqual(request.assets[1].role, 'supporting')
        self.assertEqual(request.goal.domain, 'operations')
        self.assertEqual(request.tags, ['beta', 'ops'])

    def test_distill_corpus_accepts_payload_file(self) -> None:
        payload = {
            'name': 'payload-corpus',
            'assets': [
                {'source_uri': 'file://examples/text_note.md', 'modality': 'text', 'role': 'primary'},
                {'source_uri': 'file://examples/audio_transcript.srt', 'modality': 'audio', 'role': 'supporting'},
            ],
            'goal': {'domain': 'incident-response'},
            'tags': ['payload'],
            'metadata': {'source': 'test'},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / 'corpus_payload.json'
            payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')

            service = _CapturingService()
            exit_code, output = _run_cli(
                [
                    'distill-corpus',
                    '--payload-file',
                    str(payload_path),
                ],
                service,
            )

        self.assertEqual(exit_code, 0)
        self.assertIn('skills/drafts/demo-corpus/publications/SKILL.md', output)
        self.assertEqual(len(service.corpus_requests), 1)
        request = service.corpus_requests[0]
        self.assertEqual(request.name, 'payload-corpus')
        self.assertEqual(request.goal.domain, 'incident-response')
        self.assertEqual(len(request.assets), 2)
        self.assertEqual(request.assets[0].modality.value, 'text')
        self.assertEqual(request.assets[1].modality.value, 'audio')
        self.assertEqual(request.tags, ['payload'])
        self.assertEqual(request.metadata, {'source': 'test'})

    def test_distill_corpus_supports_publication_selection_and_review_status_output(self) -> None:
        service = _CapturingService()
        exit_code, output = _run_cli(
            [
                'distill-corpus',
                '--asset',
                'text=examples/text_note.md',
                '--publication',
                'skill_json',
                '--show-publications',
            ],
            service,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn('skills/drafts/demo-corpus/publications/skill.json', output)
        self.assertIn('selected_publication=skill_json', output)
        self.assertIn('available_publications=skill_markdown,skill_json,decision_tree_json', output)
        self.assertIn(
            'review_status=review_pending decision=review_required review_task_id=review-task-1 '
            'reason_codes=traceability_low,coverage_low',
            output,
        )

    def test_distill_corpus_accepts_publication_artifact_key_style(self) -> None:
        service = _CapturingService()
        exit_code, output = _run_cli(
            [
                'distill-corpus',
                '--asset',
                'text=examples/text_note.md',
                '--publication',
                'publication_decision_tree_json',
            ],
            service,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn('skills/drafts/demo-corpus/publications/decision_tree.json', output)

    def test_export_skill_codex_target_writes_expected_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_export_bundle(root)
            exit_code, output = _run_cli(
                [
                    'export-skill',
                    '--bundle',
                    str(bundle_path),
                    '--target',
                    'codex',
                    '--output-root',
                    str(root / 'out'),
                ],
                _CapturingService(),
            )

            self.assertEqual(exit_code, 0)
            self.assertIn('target=codex', output)
            skill_path = root / 'out' / '.codex' / 'skills' / 'sample-skill' / 'SKILL.md'
            package_path = root / 'out' / '.codex' / 'skills' / 'sample-skill' / 'agent_skill_package.json'
            self.assertTrue(skill_path.is_file())
            self.assertTrue(package_path.is_file())

    def test_export_skill_claude_code_target_writes_expected_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_export_bundle(root)
            exit_code, output = _run_cli(
                [
                    'export-skill',
                    '--bundle',
                    str(bundle_path),
                    '--target',
                    'claude-code',
                    '--output-root',
                    str(root / 'out'),
                ],
                _CapturingService(),
            )

            self.assertEqual(exit_code, 0)
            self.assertIn('target=claude-code', output)
            skill_path = root / 'out' / '.claude' / 'skills' / 'sample-skill' / 'SKILL.md'
            self.assertTrue(skill_path.is_file())

    def test_export_skill_opencode_target_writes_expected_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_export_bundle(root)
            exit_code, output = _run_cli(
                [
                    'export-skill',
                    '--bundle',
                    str(bundle_path),
                    '--target',
                    'opencode',
                    '--output-root',
                    str(root / 'out'),
                ],
                _CapturingService(),
            )

            self.assertEqual(exit_code, 0)
            self.assertIn('target=opencode', output)
            skill_path = root / 'out' / '.opencode' / 'skill' / 'sample-skill' / 'SKILL.md'
            self.assertTrue(skill_path.is_file())

    def test_export_skill_portable_target_writes_expected_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_export_bundle(root)
            exit_code, output = _run_cli(
                [
                    'export-skill',
                    '--bundle',
                    str(bundle_path),
                    '--target',
                    'portable',
                    '--output-root',
                    str(root / 'out'),
                ],
                _CapturingService(),
            )

            self.assertEqual(exit_code, 0)
            self.assertIn('target=portable', output)
            skill_path = root / 'out' / 'skills' / 'portable' / 'sample-skill' / 'SKILL.md'
            self.assertTrue(skill_path.is_file())

    def test_export_skill_all_target_writes_all_layouts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_export_bundle(root)
            exit_code, output = _run_cli(
                [
                    'export-skill',
                    '--bundle',
                    str(bundle_path),
                    '--target',
                    'all',
                    '--output-root',
                    str(root / 'out'),
                ],
                _CapturingService(),
            )

            self.assertEqual(exit_code, 0)
            self.assertIn('target=codex', output)
            self.assertIn('target=claude-code', output)
            self.assertIn('target=opencode', output)
            self.assertIn('target=portable', output)
            self.assertTrue((root / 'out' / '.codex' / 'skills' / 'sample-skill' / 'SKILL.md').is_file())
            self.assertTrue((root / 'out' / '.claude' / 'skills' / 'sample-skill' / 'SKILL.md').is_file())
            self.assertTrue((root / 'out' / '.opencode' / 'skill' / 'sample-skill' / 'SKILL.md').is_file())
            self.assertTrue((root / 'out' / 'skills' / 'portable' / 'sample-skill' / 'SKILL.md').is_file())

    def test_export_skill_rejects_bundle_failing_trial_security_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle_path = self._write_export_bundle(root, unsafe=True)

            module = importlib.import_module('omni_skill_pipeline.cli')
            module = importlib.reload(module)
            with patch.object(module, 'build_service', return_value=_CapturingService()):
                with self.assertRaises(SystemExit) as exc_info:
                    module.main(
                        [
                            'export-skill',
                            '--bundle',
                            str(bundle_path),
                            '--target',
                            'portable',
                            '--output-root',
                            str(root / 'out'),
                        ]
                    )
            self.assertEqual(exc_info.exception.code, 2)

    def test_validate_skill_command_passes_for_safe_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = self._write_validated_package(root, approved=True)
            exit_code, output = _run_cli(
                [
                    'validate-skill',
                    '--package',
                    str(package_dir),
                    '--max-lines',
                    '500',
                ],
                _CapturingService(),
            )

            self.assertEqual(exit_code, 0)
            self.assertIn('status=pass', output)
            self.assertNotIn('failure_codes=', output)

    def test_validate_skill_command_reports_failure_codes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = self._write_validated_package(root, approved=False)
            exit_code, output = _run_cli(
                [
                    'validate-skill',
                    '--package',
                    str(package_dir),
                    '--max-lines',
                    '500',
                ],
                _CapturingService(),
            )

            self.assertEqual(exit_code, 2)
            self.assertIn('status=fail', output)
            self.assertIn('failure_codes=REVIEW_APPROVAL_MISSING', output)

    def test_validate_skill_command_allows_draft_only_with_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = self._write_validated_package(root, approved=False)
            exit_code, output = _run_cli(
                [
                    'validate-skill',
                    '--package',
                    str(package_dir),
                    '--max-lines',
                    '500',
                    '--allow-draft',
                ],
                _CapturingService(),
            )

            self.assertEqual(exit_code, 0)
            self.assertIn('status=pass', output)
            self.assertNotIn('failure_codes=', output)

    def test_review_queue_list_command_outputs_items(self) -> None:
        service = _CapturingService()
        exit_code, output = _run_cli(
            [
                'review-queue',
                '--action',
                'list',
                '--queue-status',
                'pending',
                '--limit',
                '10',
            ],
            service,
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertIn('items', payload)
        self.assertEqual(len(payload['items']), 1)
        self.assertEqual(payload['items'][0]['review_task_id'], 'task-1')

    def test_review_queue_approve_command_outputs_closed_item(self) -> None:
        service = _CapturingService()
        service.repository.claim_review_task(review_task_id='task-1', consumer='ops')
        exit_code, output = _run_cli(
            [
                'review-queue',
                '--action',
                'approve',
                '--review-task-id',
                'task-1',
                '--reviewer',
                'ops-lead',
                '--reason-code',
                'SAFE',
                '--review-notes',
                'manual checks passed',
                '--reviewer-edits-json',
                '{"skill_markdown_patch":"none"}',
            ],
            service,
        )
        self.assertEqual(exit_code, 0)
        payload = json.loads(output)
        self.assertEqual(payload['review_task_id'], 'task-1')
        self.assertEqual(payload['decision'], 'approve')
        self.assertEqual(payload['status'], 'published')
        self.assertEqual(payload['closed_by'], 'ops-lead')
        self.assertEqual(payload['reason_codes'], ['SAFE'])
        self.assertEqual(payload['reviewer_edits'], {'skill_markdown_patch': 'none'})

    def _write_export_bundle(self, root: Path, *, unsafe: bool = False) -> Path:
        bundle_dir = root / 'bundle'
        publication_dir = bundle_dir / 'publications'
        references_dir = publication_dir / 'references'
        references_dir.mkdir(parents=True, exist_ok=True)
        (publication_dir / 'SKILL.md').write_text(
            (
                '---\nname: "sample-skill"\ndescription: "sample description"\n---\n\n# Sample Skill\n\n'
                '## Workflow\n1. %s\n\n## Decision Rules\n- keep review\n\n## Validation\n- verify output\n\n'
                '## Failure Modes\n- do not auto publish\n'
            )
            % ('Read C:\\Users\\alice\\secrets.txt.' if unsafe else 'Review evidence before publish.'),
            encoding='utf-8',
        )
        (references_dir / 'evidence.md').write_text('# Evidence\n', encoding='utf-8')
        payload = {
            'skill': {
                'name': 'Sample Skill',
                'summary': 'Sample description',
                'skill_id': 'skill-123',
                'review_status': 'review_pending',
            },
            'skill_graph': {'graph_id': 'graph-123'},
            'corpus': {'corpus_id': 'corpus-123'},
            'evidence_units': [
                {'evidence_id': 'ev-1', 'span_ref': 'line:1'},
                {'evidence_id': 'ev-2', 'span_ref': 'line:2'},
            ],
            'asset': {'source_uri': 'file:///examples/sample.md'},
            'artifacts': {
                'publication_skill_markdown': str(publication_dir / 'SKILL.md'),
                'publication_manifest': str(publication_dir / 'manifest.json'),
            },
            'request_payload': {
                'sensitivity': 'restricted' if unsafe else 'internal',
            },
        }
        bundle_path = bundle_dir / 'bundle.json'
        bundle_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        return bundle_path

    def _write_validated_package(self, root: Path, *, approved: bool) -> Path:
        package_dir = root / 'validated-package'
        references_dir = package_dir / 'references'
        references_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / 'SKILL.md').write_text(
            '\n'.join(
                [
                    '---',
                    'name: "sample-skill"',
                    (
                        'description: "Use when the user asks to triage an incident, '
                        'validate evidence, and prepare a reviewed remediation plan."'
                    ),
                    '---',
                    '',
                    '# Sample Skill',
                    '',
                    '## Workflow',
                    '1. Collect evidence and summarize findings.',
                    '',
                    '## Decision Rules',
                    '- If evidence conflicts, escalate to reviewer.',
                    '',
                    '## Validation',
                    '- Confirm every action maps to evidence refs.',
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
                    'package_name': 'sample-skill',
                },
                ensure_ascii=False,
                indent=2,
            )
            + '\n',
            encoding='utf-8',
        )
        return package_dir


class _StubReviewQueueRepository(object):
    def __init__(self) -> None:
        self.pending = {
            'task-1': {
                'review_task_id': 'task-1',
                'skill_id': 'skill-1',
                'decision': 'review_required',
                'status': 'review_pending',
                'queue_status': 'pending',
                'reason_codes': [],
                'reviewer_edits': {},
            }
        }
        self.consumed = {}
        self.closed = {}

    def list_review_queue(self, *, queue_status: str | None = 'pending', limit: int = 100):
        normalized = str(queue_status or '').strip().lower()
        if normalized in {'', 'pending'}:
            items = [dict(item) for item in self.pending.values()]
        elif normalized == 'consumed':
            items = [dict(item) for item in self.consumed.values()]
        elif normalized == 'closed':
            items = [dict(item) for item in self.closed.values()]
        elif normalized == 'all':
            items = [*self.pending.values(), *self.consumed.values(), *self.closed.values()]
            items = [dict(item) for item in items]
        else:
            items = []
        return items[: max(0, int(limit))]

    def claim_review_task(self, review_task_id: str | None = None, *, consumer: str = 'review-consumer'):
        target = str(review_task_id or '').strip() or next(iter(self.pending.keys()), '')
        if not target:
            return None
        pending_item = self.pending.pop(target, None)
        if pending_item is None:
            return None
        claimed = dict(pending_item)
        claimed['queue_status'] = 'consumed'
        claimed['claimed_by'] = consumer.strip() or 'review-consumer'
        self.consumed[target] = claimed
        return dict(claimed)

    def consume_review_task(self, *, consumer: str = 'review-consumer'):
        return self.claim_review_task(consumer=consumer)

    def close_review_task(
        self,
        review_task_id: str,
        *,
        status: str = 'published',
        closed_by: str = 'review-operator',
        review_notes: str = '',
        decision: str | None = None,
        reason_codes=None,
        reviewer_edits=None,
    ):
        target = str(review_task_id).strip()
        if not target:
            return None
        source = self.consumed.pop(target, None) or self.pending.pop(target, None) or self.closed.get(target)
        if source is None:
            return None
        closed = dict(source)
        closed['queue_status'] = 'closed'
        closed['status'] = str(status).strip().lower() or 'published'
        if decision:
            text = str(decision).strip().lower()
            if text in {'approve', 'approved'}:
                closed['decision'] = 'approve'
            elif text in {'reject', 'rejected'}:
                closed['decision'] = 'reject'
            elif text in {'needs_rework', 'needs-rework', 'needs rework'}:
                closed['decision'] = 'needs_rework'
        closed['closed_by'] = closed_by.strip() or 'review-operator'
        closed['review_notes'] = review_notes.strip()
        if isinstance(reason_codes, list):
            closed['reason_codes'] = [str(item).strip() for item in reason_codes if str(item).strip()]
        if isinstance(reviewer_edits, dict):
            closed['reviewer_edits'] = {str(key).strip(): value for key, value in reviewer_edits.items() if str(key).strip()}
        self.closed[target] = closed
        return dict(closed)

    def update_review_task_decision(
        self,
        review_task_id: str,
        *,
        decision: str,
        reviewer: str = 'review-operator',
        reason_codes=None,
        review_notes: str = '',
        reviewer_edits=None,
        status: str | None = None,
    ):
        normalized = str(decision).strip().lower()
        if normalized in {'approved'}:
            normalized = 'approve'
        if normalized in {'rejected'}:
            normalized = 'reject'
        if normalized in {'needs-rework', 'needs rework'}:
            normalized = 'needs_rework'
        if normalized == 'approve':
            resolved_status = status or 'published'
        elif normalized == 'reject':
            resolved_status = status or 'rejected'
        else:
            resolved_status = status or 'needs_rework'
        return self.close_review_task(
            review_task_id,
            status=resolved_status,
            closed_by=reviewer,
            review_notes=review_notes,
            decision=normalized,
            reason_codes=reason_codes,
            reviewer_edits=reviewer_edits,
        )


if __name__ == '__main__':
    unittest.main()
