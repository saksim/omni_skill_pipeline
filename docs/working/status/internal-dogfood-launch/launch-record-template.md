# Internal Dogfood Launch Record Template

复制本模板为一次具体上线记录时，建议命名：

```text
docs/working/status/baselines/internal-dogfood-launch-<release_id>-summary.md
```

## Summary

| Field | Value |
| --- | --- |
| `release_id` |  |
| `commit_sha` |  |
| `branch` |  |
| `operator` |  |
| `started_at` |  |
| `ended_at` |  |
| `target_environment` | local / docker / private host |
| `decision` | READY_FOR_INTERNAL_DOGFOOD / HOLD |
| `external_launch_gate` | HOLD / READY_FOR_CONTROLLED_BETA / not_run |

## Scope Statement

本次上线只面向内部 dogfood。

明确非目标：

- 不对外承诺 Beta。
- 不宣称 GA。
- 不宣称 SaaS ready。
- 不把 fixture/simulated evidence 当成真实业务闭环。

## Commands

### Dependency Check

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip check
```

Result:

```text
TODO
```

### CI

```powershell
python scripts\ci.py --coverage-fail-under 50 --coverage-xml coverage.xml --keep-going
```

Result:

```text
TODO
```

### Official Launch Gate

```powershell
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

Result:

```text
TODO
```

Allowed interpretation:

- `HOLD` is acceptable for internal dogfood only when caused by missing real trial loop coverage.

### Internal Dogfood Gate

```powershell
python scripts\internal_launch_gate.py --output - --summary-output - --print-json
```

Result:

```text
TODO
```

### API Health

```powershell
python -m uvicorn apps.api.main:app --reload
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/v1/templates/skill
```

Result:

```text
TODO
```

### Docker Smoke

```powershell
python scripts\container_smoke.py --dry-run
python scripts\container_smoke.py --image-tag omni-skill-pipeline:dogfood --port 18000
```

Result:

```text
TODO
```

If Docker is unavailable:

```text
not_run: Docker unavailable in this environment. Local API path used instead.
```

## Known Risks

| Risk | Severity | Mitigation | Owner |
| --- | --- | --- | --- |
|  |  |  |  |

## Failures

| Failure | Category | Blocking | Action | Owner |
| --- | --- | --- | --- | --- |
|  | workflow / dependency / test / coverage / runtime | yes / no |  |  |

## Observation

| Window | Check | Result |
| --- | --- | --- |
| T+15m | `/healthz` |  |
| T+2h | errors/artifact growth/tmp growth |  |
| T+24h | internal user feedback |  |

## Rollback

Rollback triggered: yes / no

If yes:

```text
trigger:
time:
operator:
commands:
result:
follow_up:
```

## Final Decision

```text
READY_FOR_INTERNAL_DOGFOOD / HOLD
```

Decision notes:

```text
TODO
```
