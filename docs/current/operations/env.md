# Environment

## 鍒よ瘝

杩愯鍓嶅彧闇€瑕佷竴涓共鍑€鐨?Python 3.11 鐜銆佸彲閫?media binaries 鍜屾寜闇€閰嶇疆鐨?OpenAI credentials锛涗笉瑕佹妸瑙ｉ噴鍣ㄧ粷瀵硅矾寰勫啓姝诲湪鏂囨。閲屻€?
## Runtime

- Python: `3.11+`
- 瀹夎鏂瑰紡锛氫紭鍏堜娇鐢?isolated virtual environment
- Package root: `src/omni_skill_pipeline/`
- API entry: `apps/api/main.py`
- Worker entry: `apps/worker/main.py`
- CLI entry: `src/omni_skill_pipeline/cli.py`

## Quick Bootstrap

PowerShell:

```powershell
py -3.11 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

POSIX:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## OpenAI Variables

- `OPENAI_API_KEY`: 鍚敤 OpenAI provider 鎵€闇€
- `OPENAI_BASE_URL`: 鍙€夛紝鑷畾涔夊吋瀹圭鐐?- `OMNI_OPENAI_LLM_MODEL`: LLM composer model锛岄粯璁?`gpt-4.1`
- `OMNI_OPENAI_VISION_MODEL`: Vision model锛岄粯璁?`gpt-4.1-mini`
- `OMNI_OPENAI_TRANSCRIBE_MODEL`: ASR model锛岄粯璁?`gpt-4o-transcribe`
- `OMNI_OPENAI_TIMEOUT_SECONDS`: OpenAI provider request timeout in seconds锛岄粯璁?`60`
- `OMNI_OPENAI_RETRY_MAX_ATTEMPTS`: OpenAI provider 鎬诲皾璇曟鏁帮紙鍚娆¤皟鐢級锛岄粯璁?`3`
- `OMNI_OPENAI_RETRY_BASE_DELAY_SECONDS`: OpenAI provider 閫€閬垮熀鏁扮鏁帮紝榛樿 `0.5`锛堟寚鏁伴€€閬匡級
- `OMNI_OPENAI_CIRCUIT_BREAKER_CONSECUTIVE_FAILURES`: 杩炵画澶辫触鐔旀柇闃堝€硷紝榛樿 `3`
- `OMNI_OPENAI_CIRCUIT_BREAKER_COOLDOWN_SECONDS`: 鐔旀柇鍐峰嵈鏃堕棿锛堢锛夛紝榛樿 `30`
- `OMNI_OPENAI_FAILURE_BUDGET_MAX_FAILURES`: failure budget 绐楀彛鍐呮渶澶уけ璐ユ鏁帮紝榛樿 `6`
- `OMNI_OPENAI_FAILURE_BUDGET_WINDOW_SECONDS`: failure budget 缁熻绐楀彛锛堢锛夛紝榛樿 `60`
- `OMNI_TRANSCRIPTION_LANGUAGE`: 鍙€夛紝ASR language hint

## API Variables

- `OMNI_API_KEY`: 鍙€夈€傝缃悗浠?`POST /v1/distill/*` 绔偣寮哄埗鏍￠獙 `X-API-Key` 鎴?`Authorization: Bearer <key>`锛沗GET /healthz` 涓?`GET /v1/templates/skill` 淇濇寔鍏嶉壌鏉冦€?- `OMNI_RATE_LIMIT_REQUESTS`: 姣忎釜绐楀彛鍏佽璇锋眰鏁般€俙0` 琛ㄧず鍏抽棴闄愭祦锛岄粯璁?`0`銆?- `OMNI_RATE_LIMIT_WINDOW_SECONDS`: 闄愭祦绐楀彛绉掓暟锛岄粯璁?`60`銆?
## API Ops Contract Defaults

- `OMNI_API_KEY` 涓虹┖锛歞istill 鎺ュ彛涓嶉壌鏉冦€?- `OMNI_RATE_LIMIT_REQUESTS=0`锛氶檺娴佸叧闂€?- `OMNI_RATE_LIMIT_REQUESTS>0`锛氭寜 `OMNI_RATE_LIMIT_WINDOW_SECONDS` 褰㈡垚婊戝姩绐楀彛锛岃秴闄愯繑鍥?`429` 涓?`Retry-After` header銆?- 缁熶竴閿欒浣撹 `docs/current/operations/api.md` 鐨?`Error Contract`銆?
## Tenant Access (GL-08)

- OMNI_TENANT_ACCESS_JSON: optional inline tenant access-control JSON payload.
- OMNI_TENANT_ACCESS_FILE: optional path to tenant access-control JSON file (used when OMNI_TENANT_ACCESS_JSON is empty).
- When tenant access is configured, API enforces tenant key authz/quota on product routes:
  - missing tenant key -> 401
  - invalid or revoked key -> 403
  - cross-tenant scope -> 403
  - tenant quota exceeded -> 429 with Retry-After
## Health / Readiness Inputs

- `GET /healthz` 褰撳墠妫€鏌ヤ笁椤癸細
  - template path readability锛坄docs/current/contracts/SKILL.template.md`锛?  - draft directory availability锛坄skills/drafts/`锛?  - required route assembly锛坄/healthz`銆乣/v1/templates/skill`銆佷簲涓?distill 璺敱锛?- 褰撳墠鐗堟湰鏈彁渚涚嫭绔?env 瑕嗙洊 `template_path`/`draft_dir`锛涘畠浠敱 repo root 娲剧敓銆?- 褰撲换涓€妫€鏌ュけ璐ユ椂锛宍/healthz` 杩斿洖 `503` 涓?`status=degraded`銆?
## Media Variables

- `OMNI_FFMPEG_BIN`: 榛樿 `ffmpeg`
- `OMNI_FFPROBE_BIN`: 榛樿 `ffprobe`
- `OMNI_TESSERACT_BIN`: 榛樿 `tesseract`
- `OMNI_TESSERACT_LANGUAGES`: 榛樿 `eng+chi_sim`

## Video Sampling Variables

- `OMNI_KEYFRAME_INTERVAL_SECONDS`: 榛樿 `8`
- `OMNI_MAX_KEYFRAMES`: 榛樿 `6`
- `OMNI_VIDEO_SCENE_THRESHOLD`: 榛樿 `0.32`
- `OMNI_VIDEO_FRAME_DEDUPE_DISTANCE`: 榛樿 `5`

## Behavior Variable

- `OMNI_PREFER_LLM_COMPOSER`: 榛樿 `true`
- `OMNI_CONTROLLED_TRIAL_REVIEW_MODE`: 榛樿 `false`銆傝涓?`true` 鍚庯紝鎵€鏈夎捀棣忕粨鏋滈兘浼氬己鍒?`review_required`锛屼笉浼?auto-publish銆?- `OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE`: 榛樿 `controlled_trial_requires_review`銆傜敤浜庢寔涔呭寲鍙楁帶璇曡繍琛屽己鍒朵汉宸ュ鏍哥殑鍘熷洜鐮併€?- `OMNI_PORTABLE_SKILL_MARKDOWN_LINE_LIMIT`: 榛樿 `220`锛堟渶灏?`21`锛夈€傛帶鍒?portable `SKILL.md` 涓讳綋鏈€澶ц鏁帮紝闀胯瘉鎹細澶栫疆鍒?`publications/references/`銆?
## Notes

- `.env.example` 鍒楀嚭浜嗗綋鍓嶅彲閰嶇疆鍙橀噺鐨勫熀绾挎ā鏉裤€?- `docs/current/contracts/` 鏄ā鏉夸笌 schema 鐨勭湡鐩告簮銆?- `scripts/export_skill_schema.py` 浼氬鍑哄埌 `docs/current/contracts/skill.schema.json`銆?- 瑙嗛涓存椂鏂囦欢浼氳惤鍒?`.tmp_omni_media/`锛涙瘡娆′换鍔＄殑涓存椂宸ヤ綔鐩綍浼氳娓呯悊锛屼絾鏍圭洰褰曚粛寤鸿瀹氭湡 prune銆?
## Postgres Integration Test Variable

- `OMNI_TEST_POSTGRES_DSN`: Postgres DSN锛岀敤浜?`tests/test_postgres_repository_integration.py`銆乣tests/test_dual_write_repository_integration.py` 涓?`scripts/benchmark_dual_write.py`銆?
## GL-06 Artifact Repository Mode

- `OMNI_ARTIFACT_REPOSITORY_MODE`: `file`锛堥粯璁わ級/`postgres`/`dual_write`銆?- `OMNI_POSTGRES_REPOSITORY_DSN`: 褰?mode 涓?`postgres` 鎴?`dual_write` 鏃跺繀濉€?- `OMNI_DUAL_WRITE_CONTINUE_ON_SECONDARY_ERROR`: 浠?`dual_write` 妯″紡鐢熸晥锛岄粯璁?`true`銆?- `OMNI_DUAL_WRITE_SECONDARY_PREFIX`: 浠?`dual_write` 妯″紡鐢熸晥锛岄粯璁?`secondary_`銆?
Mode semantics:

- `file`: file artifact repository only (`skills/drafts/*`)銆?- `postgres`: Postgres-first repository锛堢敓浜т富璺緞锛夈€?- `dual_write`: Postgres 涓?primary锛宖ile artifact 涓?secondary debug sidecar锛屼究浜庢晠闅滄帓鏌ヤ笌鍥炴斁銆?
## Scratch Root Prune Variables

- `OMNI_TMP_MEDIA_ROOT`: scratch-root path for temporary media artifacts (default: `.tmp_omni_media`).
- `OMNI_TMP_MEDIA_RETENTION_HOURS`: retention window in hours for prune jobs (default: `24`).

## Scratch Root Prune Command

```bash
python scripts/prune_tmp_media.py --dry-run
python scripts/prune_tmp_media.py --retention-hours 24
```

## Logging Variables

- `OMNI_LOG_LEVEL`: global runtime log level for API/service/worker (default: `INFO`).
- `OMNI_LOG_FORMAT`: `json` or `plain` (default: `json`).

## GL-03 Recommended Beta Defaults

For controlled external Beta onboarding:

- Set `OMNI_CONTROLLED_TRIAL_REVIEW_MODE=true`
- Keep `OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE=controlled_trial_requires_review`
- Configure `OMNI_API_KEY` for partner-facing API environments
- Set a non-zero rate limit for safety:
  - `OMNI_RATE_LIMIT_REQUESTS=60`
  - `OMNI_RATE_LIMIT_WINDOW_SECONDS=60`

