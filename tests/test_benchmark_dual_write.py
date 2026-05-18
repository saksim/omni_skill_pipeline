from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'benchmark_dual_write.py'
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.benchmark_dual_write as benchmark_dual_write


class BenchmarkDualWriteScriptTests(unittest.TestCase):
    def test_script_smoke_runs_file_only_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'benchmark-report.json'
            draft_dir = Path(tmp_dir) / 'drafts'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--iterations',
                    '3',
                    '--skip-postgres',
                    '--output',
                    str(output_path),
                    '--draft-dir',
                    str(draft_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Benchmark mode=file_only', completed.stdout)
            self.assertIn('Benchmark report written:', completed.stdout)
            payload = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(payload.get('iterations'), 3)
            self.assertIn('file_only', payload.get('runs', {}))
            self.assertNotIn('dual_write', payload.get('runs', {}))
            self.assertEqual(payload['runs']['file_only']['summary']['count'], 3)

    def test_script_rejects_non_positive_iterations(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--iterations',
                '0',
                '--skip-postgres',
                '--output',
                '-',
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn('iterations must be > 0', completed.stderr)

    def test_postgres_mode_bootstraps_temp_schema_and_cleans_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'benchmark-report.json'
            draft_dir = Path(tmp_dir) / 'drafts'
            executed: list[str] = []
            connections: list[object] = []

            class FakeCursor:
                def execute(self, query: str, params=None) -> None:
                    executed.append(' '.join(str(query).split()))

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb) -> None:
                    return None

            class FakeConnection:
                def __init__(self) -> None:
                    self.committed = False
                    self.rolled_back = False
                    self.closed = False
                    connections.append(self)

                def cursor(self) -> FakeCursor:
                    return FakeCursor()

                def commit(self) -> None:
                    self.committed = True

                def rollback(self) -> None:
                    self.rolled_back = True

                def close(self) -> None:
                    self.closed = True

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb) -> None:
                    self.close()
                    return None

            fake_psycopg = types.SimpleNamespace(connect=lambda *args, **kwargs: FakeConnection())

            class FakePostgresRepository:
                def __init__(self, dsn: str, *, connect) -> None:
                    self.dsn = dsn
                    self.connect = connect

                def save_bundle(self, bundle) -> dict[str, str]:
                    connection = self.connect(self.dsn)
                    connection.close()
                    return {'skill': 'postgres://skills/%s' % bundle.skill.skill_id}

            with mock.patch.object(benchmark_dual_write, '_load_psycopg', return_value=fake_psycopg), \
                mock.patch.object(benchmark_dual_write, 'PostgresRepository', FakePostgresRepository):
                completed_code = benchmark_dual_write.main_with_args(
                    [
                        '--iterations',
                        '2',
                        '--postgres-dsn',
                        'postgresql://example',
                        '--output',
                        str(output_path),
                        '--draft-dir',
                        str(draft_dir),
                    ]
                )

            self.assertEqual(completed_code, 0)
            payload = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertTrue(payload['run_postgres'])
            self.assertTrue(payload['postgres_schema_bootstrapped'])
            self.assertEqual(payload['runs']['dual_write']['summary']['count'], 2)
            self.assertTrue(any(command.startswith('CREATE SCHEMA') for command in executed))
            self.assertTrue(any(command.startswith('SET search_path TO') for command in executed))
            self.assertTrue(any(command.startswith('CREATE TABLE skills') for command in executed))
            self.assertTrue(any(command.startswith('DROP SCHEMA IF EXISTS') for command in executed))


if __name__ == '__main__':
    unittest.main()
