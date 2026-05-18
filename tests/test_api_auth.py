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


def _build_settings(api_key: str | None):
    return SimpleNamespace(
        api_key=api_key,
        template_path=REPO_ROOT / 'docs' / 'current' / 'contracts' / 'SKILL.template.md',
    )


def _build_client(api_key: str | None):
    with (
        patch('omni_skill_pipeline.service.build_service', return_value=_StubService()),
        patch('omni_skill_pipeline.config.load_settings', return_value=_build_settings(api_key)),
    ):
        module = importlib.import_module('omni_skill_pipeline.api_app')
        module = importlib.reload(module)
        app = module.create_app()
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiAuthTests(unittest.TestCase):
    def test_missing_api_key_returns_401_when_auth_enabled(self) -> None:
        client = _build_client('top-secret')
        response = client.post('/v1/distill/text', json={'content': 'incident timeline'})
        self.assertEqual(response.status_code, 401)
        payload = response.json()['error']
        self.assertEqual(payload['type'], 'http')
        self.assertEqual(payload['code'], 'http_error')
        self.assertEqual(payload['message'], 'Missing API key.')

    def test_invalid_api_key_returns_403_when_auth_enabled(self) -> None:
        client = _build_client('top-secret')
        response = client.post(
            '/v1/distill/text',
            json={'content': 'incident timeline'},
            headers={'X-API-Key': 'wrong-key'},
        )
        self.assertEqual(response.status_code, 403)
        payload = response.json()['error']
        self.assertEqual(payload['type'], 'http')
        self.assertEqual(payload['code'], 'http_error')
        self.assertEqual(payload['message'], 'Invalid API key.')

    def test_valid_x_api_key_header_allows_request(self) -> None:
        client = _build_client('top-secret')
        response = client.post(
            '/v1/distill/text',
            json={'content': 'incident timeline'},
            headers={'X-API-Key': 'top-secret'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True})

    def test_valid_bearer_authorization_header_allows_request(self) -> None:
        client = _build_client('top-secret')
        response = client.post(
            '/v1/distill/text',
            json={'content': 'incident timeline'},
            headers={'Authorization': 'Bearer top-secret'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True})

    def test_auth_can_be_disabled_with_empty_api_key_setting(self) -> None:
        client = _build_client('')
        response = client.post('/v1/distill/text', json={'content': 'incident timeline'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True})


if __name__ == '__main__':
    unittest.main()
