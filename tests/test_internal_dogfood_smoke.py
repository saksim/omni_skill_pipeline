from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class _FakeResponse(object):
    def __init__(self, *, status: int, payload) -> None:
        self.status = status
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        if isinstance(self.payload, str):
            return self.payload.encode("utf-8")
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


class InternalDogfoodSmokeScriptTests(unittest.TestCase):
    def test_dry_run_outputs_expected_plan(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/internal_dogfood_smoke.py",
                "--dry-run",
                "--base-url",
                "http://127.0.0.1:18000",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Plan: GET http://127.0.0.1:18000/healthz", completed.stdout)
        self.assertIn("Plan: GET http://127.0.0.1:18000/v1/templates/skill", completed.stdout)
        self.assertIn("Plan: POST http://127.0.0.1:18000/v1/distill/text", completed.stdout)
        self.assertIn("queue_status=pending", completed.stdout)

    def test_happy_path_report_passes_and_traces_review_task(self) -> None:
        module = importlib.import_module("scripts.internal_dogfood_smoke")
        module = importlib.reload(module)
        seen_urls: list[str] = []

        def fake_urlopen(request, timeout):
            self.assertEqual(timeout, 5.0)
            url = request.full_url
            seen_urls.append(url)
            if url.endswith("/healthz"):
                return _FakeResponse(status=200, payload={"status": "ready"})
            if url.endswith("/v1/templates/skill"):
                return _FakeResponse(status=200, payload="# template")
            if url.endswith("/v1/distill/text"):
                request_payload = json.loads(request.data.decode("utf-8"))
                self.assertEqual(request_payload["goal"]["audience"], "self")
                return _FakeResponse(
                    status=200,
                    payload={
                        "skill_markdown": "# Internal smoke skill\n",
                        "review_status": "review_pending",
                        "review_task": {
                            "review_task_id": "task-smoke-1",
                            "status": "review_pending",
                        },
                    },
                )
            if "/v1/review/queue" in url:
                return _FakeResponse(
                    status=200,
                    payload={
                        "items": [
                            {
                                "review_task_id": "task-smoke-1",
                                "queue_status": "pending",
                            }
                        ]
                    },
                )
            raise AssertionError("Unexpected URL: %s" % url)

        with patch.object(module.urllib.request, "urlopen", side_effect=fake_urlopen):
            report = module._build_report(
                module.SmokeConfig(
                    base_url="http://127.0.0.1:8000",
                    api_key="",
                    timeout_seconds=5.0,
                    title="Smoke",
                    content="Smoke content",
                    dry_run=False,
                )
            )

        self.assertEqual(report["decision"], "PASS")
        self.assertEqual(report["review_task_id"], "task-smoke-1")
        self.assertEqual(report["fail_count"], 0)
        self.assertTrue(any("/v1/review/queue" in url for url in seen_urls))

    def test_review_queue_trace_fails_when_distilled_task_is_missing(self) -> None:
        module = importlib.import_module("scripts.internal_dogfood_smoke")
        module = importlib.reload(module)

        def fake_urlopen(request, timeout):
            url = request.full_url
            if url.endswith("/healthz"):
                return _FakeResponse(status=200, payload={"status": "ready"})
            if url.endswith("/v1/templates/skill"):
                return _FakeResponse(status=200, payload="# template")
            if url.endswith("/v1/distill/text"):
                request_payload = json.loads(request.data.decode("utf-8"))
                self.assertEqual(request_payload["goal"]["audience"], "self")
                return _FakeResponse(
                    status=200,
                    payload={
                        "skill_markdown": "# Internal smoke skill\n",
                        "review_status": "review_pending",
                        "review_task": {"review_task_id": "task-smoke-1"},
                    },
                )
            if "/v1/review/queue" in url:
                return _FakeResponse(status=200, payload={"items": []})
            raise AssertionError("Unexpected URL: %s" % url)

        with patch.object(module.urllib.request, "urlopen", side_effect=fake_urlopen):
            report = module._build_report(
                module.SmokeConfig(
                    base_url="http://127.0.0.1:8000",
                    api_key="",
                    timeout_seconds=5.0,
                    title="Smoke",
                    content="Smoke content",
                    dry_run=False,
                )
            )

        self.assertEqual(report["decision"], "FAIL")
        self.assertEqual(report["fail_count"], 1)
        self.assertIn("review_queue_trace", [check["name"] for check in report["checks"]])

    def test_happy_path_can_write_json_and_markdown_evidence(self) -> None:
        module = importlib.import_module("scripts.internal_dogfood_smoke")
        module = importlib.reload(module)

        def fake_urlopen(request, timeout):
            url = request.full_url
            if url.endswith("/healthz"):
                return _FakeResponse(status=200, payload={"status": "ready"})
            if url.endswith("/v1/templates/skill"):
                return _FakeResponse(status=200, payload="# template")
            if url.endswith("/v1/distill/text"):
                return _FakeResponse(
                    status=200,
                    payload={
                        "skill_markdown": "# Internal smoke skill\n",
                        "review_status": "review_pending",
                        "review_task": {"review_task_id": "task-smoke-1"},
                    },
                )
            if "/v1/review/queue" in url:
                return _FakeResponse(
                    status=200,
                    payload={"items": [{"review_task_id": "task-smoke-1", "queue_status": "pending"}]},
                )
            raise AssertionError("Unexpected URL: %s" % url)

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "smoke-report.json"
            summary_path = Path(tmp_dir) / "smoke-summary.md"
            with patch.object(module.urllib.request, "urlopen", side_effect=fake_urlopen):
                exit_code = module.main(
                    [
                        "--base-url",
                        "http://127.0.0.1:8000",
                        "--output",
                        str(report_path),
                        "--summary-output",
                        str(summary_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["decision"], "PASS")
            self.assertIn("Internal Dogfood API Smoke Summary", summary_path.read_text(encoding="utf-8"))
