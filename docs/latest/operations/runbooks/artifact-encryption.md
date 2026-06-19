# Artifact Encryption Runbook

## Purpose

Use this runbook to enable optional local encryption for file-backed artifacts
and review queue files in the internal dogfood path.

This runbook applies to `v0.2.3-internal.1` and later. It does not provide
Vault/KMS integration, automated key rotation, K8s secret management, or
Postgres encryption.

## Scope

Covered:

- `FileArtifactRepository` artifacts under `skills/drafts/`
- review queue files under `skills/drafts/review_queue/`
- local developer or internal dogfood environments using repository mode `file`

Not covered:

- Postgres repository encryption
- dual-write primary database encryption
- cloud secret manager integration
- production key escrow or rotation automation
- retroactive bulk migration of old plaintext artifacts

## Preconditions

- Python 3.11 environment is active.
- Dependencies are installed with `python -m pip install -r requirements-dev.txt`
  or from an installed release wheel.
- `cryptography` is installed. It is a runtime dependency in `pyproject.toml`.
- The operator has decided where to store the Fernet key outside the repository.

Never commit `OMNI_ARTIFACT_ENCRYPTION_KEY` or generated keys.

## Generate A Key

```bash
python -c "from omni_skill_pipeline.artifact_crypto import generate_fernet_key; print(generate_fernet_key())"
```

Store the output in a local secret store, password manager, or CI secret. The
same key is required to read encrypted artifacts later.

## Enable Encryption

PowerShell:

```powershell
$env:OMNI_ARTIFACT_REPOSITORY_MODE = "file"
$env:OMNI_ARTIFACT_ENCRYPTION_MODE = "fernet"
$env:OMNI_ARTIFACT_ENCRYPTION_KEY = "<generated-key>"
$env:OMNI_ARTIFACT_ENCRYPTION_KEY_ID = "internal-dogfood-local"
```

POSIX:

```bash
export OMNI_ARTIFACT_REPOSITORY_MODE=file
export OMNI_ARTIFACT_ENCRYPTION_MODE=fernet
export OMNI_ARTIFACT_ENCRYPTION_KEY="<generated-key>"
export OMNI_ARTIFACT_ENCRYPTION_KEY_ID="internal-dogfood-local"
```

## Smoke Test

Run a small text distillation:

```bash
python -m omni_skill_pipeline.cli distill-text \
  --title "Artifact encryption smoke" \
  --content "Internal dogfood artifact encryption smoke." \
  --domain operations
```

Then inspect one generated JSON artifact under `skills/drafts/`. It should be a
JSON encryption envelope with:

- `schema_version`: `omni_artifact_encryption.v1`
- `algorithm`: `fernet`
- `key_id`: the configured key id
- `ciphertext`: encrypted payload

The original plaintext should not be readable in the stored file.

## Review Queue Smoke

When review-required output is generated, the pending queue item is also
encrypted. The configured repository can still list and claim it:

```bash
python -m omni_skill_pipeline.cli review-queue --action list --queue-status pending --limit 5
python -m omni_skill_pipeline.cli review-queue --action claim --consumer encryption-smoke
```

If the key is missing or wrong, encrypted queue entries are not readable. Restore
the correct key before retrying.

## Disable Encryption

Unset the encryption variables or set mode to `off`:

PowerShell:

```powershell
$env:OMNI_ARTIFACT_ENCRYPTION_MODE = "off"
$env:OMNI_ARTIFACT_ENCRYPTION_KEY = ""
```

POSIX:

```bash
export OMNI_ARTIFACT_ENCRYPTION_MODE=off
unset OMNI_ARTIFACT_ENCRYPTION_KEY
```

Important behavior:

- New artifacts are plaintext when encryption is off.
- Old plaintext artifacts remain readable while encryption is off.
- Existing encrypted artifacts require the original key; encryption-off mode
  does not silently decrypt them.

## Manual Key Rotation

Automated key rotation is not implemented. To rotate manually:

1. Stop writers that use `FileArtifactRepository`.
2. Preserve the old key until all required encrypted artifacts are migrated or
   intentionally expired.
3. Generate a new Fernet key.
4. Set `OMNI_ARTIFACT_ENCRYPTION_KEY` to the new key and update
   `OMNI_ARTIFACT_ENCRYPTION_KEY_ID`.
5. Run the smoke test above.
6. Record the rotation date, old key id, new key id, and operator in the
   operations log.

Do not delete the old key while old encrypted artifacts may still need to be
read.

## Troubleshooting

| Symptom | Likely Cause | Action |
| --- | --- | --- |
| `OMNI_ARTIFACT_ENCRYPTION_KEY is required` | `fernet` mode is enabled without a key. | Set `OMNI_ARTIFACT_ENCRYPTION_KEY` or turn mode `off`. |
| `must be a urlsafe base64-encoded 32-byte Fernet key` | Key is malformed. | Regenerate using `generate_fernet_key`. |
| Review queue list is empty after enabling encryption | Existing encrypted entries cannot be decrypted by the current key. | Restore the original key or inspect queue files with the correct environment. |
| Plaintext appears in new artifacts | Encryption mode is unset/off or process was started before env changes. | Restart the process and verify environment variables. |
| Encrypted artifacts unreadable after disabling encryption | Encrypted files still require the key. | Re-enable `fernet` with the original key for read operations. |

## Verification Commands

```bash
python -m unittest tests.test_artifact_encryption tests.test_openai_provider_config tests.test_service_factory_split
python scripts/doc_sync.py --output -
```

For full release packaging, use
[GitHub Release Workflow](github-release-workflow.md). For Docker/Postgres
production claims, continue to the stricter infrastructure runbooks instead of
treating this local encryption runbook as sufficient evidence.
