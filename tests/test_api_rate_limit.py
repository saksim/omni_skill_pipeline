from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


class _StubBundle(object):
    def to_dict(self) -> dict[str, bool]:
        return {'ok': True}


class _StubService(object):
    def distill_text(self, request):
        return _StubBundle()

    def distill_audio(self, request):
        return _StubBundle()

    def distill_image(self, request):
        return _StubBundle()

    def distill_tabular(self, request):
        return _StubBundle()

    def distill_video(self, request):
        return _StubBundle()


def _build_settings(
    *,
    api_key: str | None,
    rate_limit_requests: int,
    rate_limit_window_seconds: int,
):
    return SimpleNamespace(
        api_key=api_key,
        rate_limit_requests=rate_limit_requests,
        rate_limit_window_seconds=rate_limit_window_seconds,
        tenant_access_json='',
        tenant_access_file='',
        template_path=REPO_ROOT / 'docs' / 'current' / 'contracts' / 'SKILL.template.md',
    )


def _build_client(
    *,
    api_key: str | None,
    rate_limit_requests: int,
    rate_limit_window_seconds: int,
):
    with (
        patch('omni_skill_pipeline.service.build_service', return_value=_StubService()),
        patch(
            'omni_skill_pipeline.config.load_settings',
            return_value=_build_settings(
                api_key=api_key,
                rate_limit_requests=rate_limit_requests,
                rate_limit_window_seconds=rate_limit_window_seconds,
            ),
        ),
    ):
        module = importlib.import_module('omni_skill_pipeline.api_app')
        module = importlib.reload(module)
        app = module.create_app()
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiRateLimitTests(unittest.TestCase):
    def test_rate_limit_by_ip_returns_429_after_quota(self) -> None:
        client = _build_client(
            api_key='',
            rate_limit_requests=1,
            rate_limit_window_seconds=60,
        )
        payload = {'content': 'incident timeline'}

        first = client.post('/v1/distill/text', json=payload)
        second = client.post('/v1/distill/text', json=payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json()['error']['code'], 'http_error')
        self.assertEqual(second.json()['error']['message'], 'Rate limit exceeded.')
        self.assertIn('Retry-After', second.headers)

    def test_rate_limit_prefers_api_key_isolation(self) -> None:
        client = _build_client(
            api_key='',
            rate_limit_requests=1,
            rate_limit_window_seconds=60,
        )
        payload = {'content': 'incident timeline'}

        first_a = client.post('/v1/distill/text', json=payload, headers={'X-API-Key': 'tenant-a'})
        second_a = client.post('/v1/distill/text', json=payload, headers={'X-API-Key': 'tenant-a'})
        first_b = client.post('/v1/distill/text', json=payload, headers={'X-API-Key': 'tenant-b'})

        self.assertEqual(first_a.status_code, 200)
        self.assertEqual(second_a.status_code, 429)
        self.assertEqual(first_b.status_code, 200)

    def test_rate_limit_can_be_disabled(self) -> None:
        client = _build_client(
            api_key='',
            rate_limit_requests=0,
            rate_limit_window_seconds=60,
        )
        payload = {'content': 'incident timeline'}

        first = client.post('/v1/distill/text', json=payload)
        second = client.post('/v1/distill/text', json=payload)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)


if __name__ == '__main__':
    unittest.main()
