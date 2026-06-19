from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from omni_skill_pipeline.models import utc_now_iso

ENCRYPTION_SCHEMA_VERSION = 'omni_artifact_encryption.v1'
FERNET_ALGORITHM = 'fernet'


class ArtifactEncryptionError(ValueError):
    pass


def generate_fernet_key() -> str:
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ArtifactEncryptionError(
            'cryptography is required to generate artifact encryption keys.'
        ) from exc
    return Fernet.generate_key().decode('ascii')


def is_encrypted_artifact_payload(value: str) -> bool:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return False
    return isinstance(payload, dict) and payload.get('schema_version') == ENCRYPTION_SCHEMA_VERSION


@dataclass(frozen=True)
class ArtifactEncryptor:
    key: str
    key_id: str = 'default'

    def __post_init__(self) -> None:
        normalized_key = str(self.key or '').strip()
        if not normalized_key:
            raise ArtifactEncryptionError('OMNI_ARTIFACT_ENCRYPTION_KEY is required when artifact encryption is enabled.')
        normalized_key_id = str(self.key_id or '').strip() or 'default'
        object.__setattr__(self, 'key', normalized_key)
        object.__setattr__(self, 'key_id', normalized_key_id)
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise ArtifactEncryptionError(
                'cryptography is required when artifact encryption is enabled.'
            ) from exc
        try:
            object.__setattr__(self, '_fernet', Fernet(normalized_key.encode('ascii')))
        except (TypeError, ValueError) as exc:
            raise ArtifactEncryptionError(
                'OMNI_ARTIFACT_ENCRYPTION_KEY must be a urlsafe base64-encoded 32-byte Fernet key.'
            ) from exc

    def encrypt_text(self, plaintext: str) -> str:
        token = self._fernet.encrypt(str(plaintext).encode('utf-8')).decode('ascii')
        envelope: dict[str, Any] = {
            'schema_version': ENCRYPTION_SCHEMA_VERSION,
            'algorithm': FERNET_ALGORITHM,
            'key_id': self.key_id,
            'encrypted_at_utc': utc_now_iso(),
            'ciphertext': token,
        }
        return json.dumps(envelope, ensure_ascii=False, indent=2) + '\n'

    def decrypt_text(self, value: str) -> str:
        if not is_encrypted_artifact_payload(value):
            return value
        payload = json.loads(value)
        if payload.get('algorithm') != FERNET_ALGORITHM:
            raise ArtifactEncryptionError('Unsupported artifact encryption algorithm: %s' % payload.get('algorithm'))
        ciphertext = str(payload.get('ciphertext', '')).strip()
        if not ciphertext:
            raise ArtifactEncryptionError('Encrypted artifact envelope is missing ciphertext.')
        try:
            plaintext = self._fernet.decrypt(ciphertext.encode('ascii'))
        except Exception as exc:
            raise ArtifactEncryptionError('Unable to decrypt artifact payload with the configured key.') from exc
        return plaintext.decode('utf-8')
