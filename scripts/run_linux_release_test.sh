#!/usr/bin/env bash
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

RELEASE_ID="${RELEASE_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-release-artifacts}"
ARTIFACT_DIR="${ARTIFACT_ROOT}/${RELEASE_ID}"
LOG_DIR="${ARTIFACT_DIR}/logs"
META_DIR="${ARTIFACT_DIR}/meta"
BASELINE_DIR="${REPO_ROOT}/docs/current/status/baselines"
VERSIONED_RUNTIME_IMAGE_TAG="${VERSIONED_RUNTIME_IMAGE_TAG:-omni-skill-pipeline:${RELEASE_ID}}"
TEST_IMAGE_TAG="${TEST_IMAGE_TAG:-omni-skill-pipeline:test-${RELEASE_ID}}"
TEST_IMAGE_ALIAS="${TEST_IMAGE_ALIAS:-omni-skill-pipeline:test}"
RUNTIME_IMAGE_TAG="${RUNTIME_IMAGE_TAG:-${VERSIONED_RUNTIME_IMAGE_TAG}}"
RUNTIME_IMAGE_ALIAS="${RUNTIME_IMAGE_ALIAS:-omni-skill-pipeline:beta}"
SMOKE_PORT="${SMOKE_PORT:-18000}"
API_ACCEPTANCE_PORT="${API_ACCEPTANCE_PORT:-18001}"
API_CONTAINER_NAME="${API_CONTAINER_NAME:-omni-skill-beta-acceptance-${RELEASE_ID}}"
API_DRAFTS_VOLUME="${API_DRAFTS_VOLUME:-omni_skill_release_${RELEASE_ID}_drafts}"
API_PUBLISHED_VOLUME="${API_PUBLISHED_VOLUME:-omni_skill_release_${RELEASE_ID}_published}"
API_TMP_MEDIA_VOLUME="${API_TMP_MEDIA_VOLUME:-omni_skill_release_${RELEASE_ID}_tmp_media}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-.env.runtime}"
COVERAGE_FAIL_UNDER="${COVERAGE_FAIL_UNDER:-50}"
DRY_RUN=0

mkdir -p "${LOG_DIR}" "${META_DIR}" "${BASELINE_DIR}"

STAGE_NAMES=()
STAGE_CODES=()
STAGE_LOGS=()
STAGE_STATUS=()

cleanup_acceptance_container() {
  docker rm -f "${API_CONTAINER_NAME}" >/dev/null 2>&1 || true
  docker volume rm "${API_DRAFTS_VOLUME}" "${API_PUBLISHED_VOLUME}" "${API_TMP_MEDIA_VOLUME}" >/dev/null 2>&1 || true
}

trap cleanup_acceptance_container EXIT

usage() {
  cat <<'EOF'
Usage: bash scripts/run_linux_release_test.sh

Run this on the bare Linux host after cloning the repo. Do not enter the
container manually first; this script builds the test/runtime images and runs
the validation commands inside Docker for you.

Environment overrides:
  RELEASE_ID                   Release id used in image/artifact names.
  ARTIFACT_ROOT                Output root directory. Default: release-artifacts
  TEST_IMAGE_TAG               Test image tag. Default: omni-skill-pipeline:test-$RELEASE_ID
  TEST_IMAGE_ALIAS             Extra test image alias. Default: omni-skill-pipeline:test
  RUNTIME_IMAGE_TAG            Runtime image tag used by tests. Default: omni-skill-pipeline:$RELEASE_ID
  RUNTIME_IMAGE_ALIAS          Extra runtime image alias. Default: omni-skill-pipeline:beta
  VERSIONED_RUNTIME_IMAGE_TAG  Versioned runtime tag. Default: omni-skill-pipeline:$RELEASE_ID
  RUNTIME_ENV_FILE             Runtime env file for API acceptance. Default: .env.runtime
  OMNI_TEST_POSTGRES_DSN       Optional Postgres DSN for GA/release gates.
  OMNI_API_KEY                 Optional API key header for acceptance if auth is enabled.
  COVERAGE_FAIL_UNDER          Coverage gate threshold. Default: 50
  SMOKE_PORT                   Container smoke host port. Default: 18000
  API_ACCEPTANCE_PORT          API acceptance host port. Default: 18001

Options:
  --dry-run                    Print and record the release-test plan without
                               building images or running containers.

Outputs:
  release-artifacts/<RELEASE_ID>/logs/*.log
  release-artifacts/<RELEASE_ID>/logs/*.exit
  release-artifacts/<RELEASE_ID>/baselines/*
  release-artifacts/<RELEASE_ID>/summary.tsv
  release-artifacts/<RELEASE_ID>/summary.json
  release-artifacts-<RELEASE_ID>.tar.gz
EOF
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

record_stage() {
  local name="$1"
  local code="$2"
  local log_path="$3"
  local status="${4:-run}"
  STAGE_NAMES+=("${name}")
  STAGE_CODES+=("${code}")
  STAGE_LOGS+=("${log_path}")
  STAGE_STATUS+=("${status}")
  printf '%s\n' "${code}" > "${LOG_DIR}/${name}.exit"
}

stage_succeeded() {
  local name="$1"
  local i
  for i in "${!STAGE_NAMES[@]}"; do
    if [[ "${STAGE_NAMES[$i]}" == "${name}" ]]; then
      [[ "${STAGE_CODES[$i]}" == "0" ]]
      return $?
    fi
  done
  return 1
}

run_step() {
  local name="$1"
  shift
  local log_path="${LOG_DIR}/${name}.log"
  echo "===== ${name} ====="
  (
    echo "release_id=${RELEASE_ID}"
    echo "stage=${name}"
    echo "started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    "$@"
    code=$?
    echo "finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "exit=${code}"
    exit "${code}"
  ) 2>&1 | tee "${log_path}"
  local code="${PIPESTATUS[0]}"
  record_stage "${name}" "${code}" "${log_path}" "run"
  return 0
}

plan_step() {
  local name="$1"
  shift
  local log_path="${LOG_DIR}/${name}.log"
  echo "===== ${name} ====="
  {
    echo "release_id=${RELEASE_ID}"
    echo "stage=${name}"
    echo "started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "dry_run=true"
    printf 'Plan:'
    printf ' %q' "$@"
    printf '\n'
    echo "finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "exit=0"
  } 2>&1 | tee "${log_path}"
  record_stage "${name}" "0" "${log_path}" "planned"
  return 0
}

run_or_plan_step() {
  if [[ "${DRY_RUN}" == "1" ]]; then
    plan_step "$@"
  else
    run_step "$@"
  fi
}

skip_step() {
  local name="$1"
  shift
  local reason="$*"
  local log_path="${LOG_DIR}/${name}.log"
  echo "===== ${name} ====="
  {
    echo "release_id=${RELEASE_ID}"
    echo "stage=${name}"
    echo "started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "skipped=true"
    echo "reason=${reason}"
    echo "finished_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "exit=99"
  } 2>&1 | tee "${log_path}"
  record_stage "${name}" "99" "${log_path}" "skipped"
  return 0
}

runtime_image_ready() {
  stage_succeeded build_runtime_image
}

capture_meta() {
  {
    echo "release_id=${RELEASE_ID}"
    echo "repo_root=${REPO_ROOT}"
    echo "started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "${META_DIR}/run.env"
  git rev-parse HEAD > "${META_DIR}/git-head.txt" 2>&1 || true
  git status --short > "${META_DIR}/git-status.txt" 2>&1 || true
  docker version > "${META_DIR}/docker-version.txt" 2>&1 || true
  docker info > "${META_DIR}/docker-info.txt" 2>&1 || true
}

preflight_source_tree() {
  local code=0
  local required_paths=(
    "Dockerfile"
    "Dockerfile.test"
    "Dockerfile.test.dockerignore"
    ".dockerignore"
    "pyproject.toml"
    "requirements-dev.txt"
    "README.md"
    "src/omni_skill_pipeline"
    "src/omni_skill_pipeline/adapters/__init__.py"
    "src/omni_skill_pipeline/adapters/audio.py"
    "src/omni_skill_pipeline/adapters/image.py"
    "src/omni_skill_pipeline/adapters/tabular.py"
    "src/omni_skill_pipeline/adapters/text.py"
    "src/omni_skill_pipeline/adapters/video.py"
    "apps/api/main.py"
    "scripts/run_ci.py"
    "scripts/run_container_smoke.py"
    "scripts/run_linux_validation_suite.py"
    "scripts/run_release_switch_validation.py"
    "tests"
    "docs/current/contracts/SKILL.template.md"
    "docs/current/contracts/skill.schema.json"
    "docs/current/contracts/skill-graph.schema.json"
  )
  local path

  for path in "${required_paths[@]}"; do
    if [[ ! -e "${path}" ]]; then
      echo "missing required release source path: ${path}" >&2
      code=1
    fi
  done

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    local ignored_output
    ignored_output="$(git check-ignore -v docs/current/contracts docs/current/contracts/SKILL.template.md docs/current/contracts/skill.schema.json docs/current/contracts/skill-graph.schema.json || true)"
    if [[ -n "${ignored_output}" ]]; then
      printf '%s\n' "${ignored_output}" >&2
      code=1
    fi
  fi

  return "${code}"
}

ensure_runtime_env_file() {
  if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
    printf '%s\n' "${RUNTIME_ENV_FILE}"
    return 0
  fi

  local generated="${META_DIR}/generated.env.runtime"
  cat > "${generated}" <<'EOF'
OMNI_LOG_FORMAT=json
OMNI_LOG_LEVEL=INFO
OMNI_TMP_MEDIA_ROOT=/app/.tmp_omni_media
OPENAI_API_KEY=
OMNI_API_KEY=
EOF
  chmod 600 "${generated}" || true
  printf '%s\n' "${generated}"
}

docker_curl() {
  docker run --rm --network host "${TEST_IMAGE_TAG}" curl "$@"
}

docker_image_exists() {
  docker image inspect "$1" >/dev/null 2>&1
}

poll_url() {
  local url="$1"
  local timeout_seconds="${2:-30}"
  local interval_seconds="${3:-1}"
  local deadline=$((SECONDS + timeout_seconds))

  while [[ "${SECONDS}" -le "${deadline}" ]]; do
    if docker_curl -fsS --max-time 5 "${url}"; then
      return 0
    fi
    sleep "${interval_seconds}"
  done
  return 1
}

api_acceptance() {
  local runtime_env
  runtime_env="$(ensure_runtime_env_file)"
  local base_url="http://127.0.0.1:${API_ACCEPTANCE_PORT}"
  local code=0
  local auth_args=()

  if [[ -n "${OMNI_API_KEY:-}" ]]; then
    auth_args=(-H "X-API-Key: ${OMNI_API_KEY}")
  fi

  if ! docker_image_exists "${RUNTIME_IMAGE_TAG}"; then
    echo "Runtime image not found locally: ${RUNTIME_IMAGE_TAG}" >&2
    echo "Build runtime image before API acceptance; refusing to let docker run pull this tag from a registry." >&2
    return 125
  fi

  docker rm -f "${API_CONTAINER_NAME}" >/dev/null 2>&1 || true
  docker run -d \
    --name "${API_CONTAINER_NAME}" \
    -p "${API_ACCEPTANCE_PORT}:8000" \
    --env-file "${runtime_env}" \
    -v "${API_DRAFTS_VOLUME}:/app/skills/drafts" \
    -v "${API_PUBLISHED_VOLUME}:/app/skills/published" \
    -v "${API_TMP_MEDIA_VOLUME}:/app/.tmp_omni_media" \
    "${RUNTIME_IMAGE_TAG}"
  local run_code=$?
  if [[ "${run_code}" != "0" ]]; then
    return "${run_code}"
  fi

  poll_url "${base_url}/healthz" 30 1
  code=$?
  if [[ "${code}" != "0" ]]; then
    docker logs --tail 300 "${API_CONTAINER_NAME}" || true
    docker rm -f "${API_CONTAINER_NAME}" >/dev/null 2>&1 || true
    docker volume rm "${API_DRAFTS_VOLUME}" "${API_PUBLISHED_VOLUME}" "${API_TMP_MEDIA_VOLUME}" >/dev/null 2>&1 || true
    return "${code}"
  fi
  docker_curl -fsS --max-time 10 "${base_url}/v1/templates/skill" >/dev/null || code=$?
  docker_curl -fsS -X POST "${base_url}/v1/distill/text" \
    --max-time 30 \
    -H "Content-Type: application/json" \
    "${auth_args[@]}" \
    -d '{"title":"Release Smoke","file_path":"docs/current/contracts/SKILL.template.md","goal":{"domain":"release_smoke"}}' \
    >/dev/null || code=$?

  docker logs --tail 300 "${API_CONTAINER_NAME}" || true
  docker rm -f "${API_CONTAINER_NAME}" >/dev/null 2>&1 || true
  docker volume rm "${API_DRAFTS_VOLUME}" "${API_PUBLISHED_VOLUME}" "${API_TMP_MEDIA_VOLUME}" >/dev/null 2>&1 || true
  return "${code}"
}

copy_evidence() {
  rm -rf "${ARTIFACT_DIR}/baselines"
  mkdir -p "${ARTIFACT_DIR}/baselines"
  cp -a "${BASELINE_DIR}/." "${ARTIFACT_DIR}/baselines/" 2>/dev/null || true
}

read_release_decision() {
  if [[ "${DRY_RUN}" == "1" ]]; then
    printf 'dry_run'
    return 0
  fi

  local report="${BASELINE_DIR}/e13-release-switch-decision-report.json"
  if [[ ! -f "${report}" ]]; then
    printf 'missing'
    return 0
  fi
  grep -m1 '"decision"' "${report}" \
    | sed -E 's/.*"decision"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' \
    || printf 'unknown'
}

write_summary() {
  local decision="$1"
  local overall="PASS"
  local stage_failed=0
  local i
  for i in "${!STAGE_NAMES[@]}"; do
    if [[ "${STAGE_CODES[$i]}" != "0" ]]; then
      overall="FAIL"
      stage_failed=1
    fi
  done
  if [[ "${DRY_RUN}" == "1" ]]; then
    if [[ "${stage_failed}" == "0" ]]; then
      overall="PLANNED"
    fi
  elif [[ "${decision}" != "GO" ]]; then
    overall="FAIL"
  fi

  {
    printf 'stage\texit_code\tstatus\tlog\n'
    for i in "${!STAGE_NAMES[@]}"; do
      printf '%s\t%s\t%s\t%s\n' "${STAGE_NAMES[$i]}" "${STAGE_CODES[$i]}" "${STAGE_STATUS[$i]}" "${STAGE_LOGS[$i]}"
    done
    printf 'release_switch_decision\t%s\treport\t%s\n' "${decision}" "${BASELINE_DIR}/e13-release-switch-decision-report.json"
    printf 'overall\t%s\tresult\t%s\n' "${overall}" "${ARTIFACT_DIR}"
  } > "${ARTIFACT_DIR}/summary.tsv"

  {
    printf '{\n'
    printf '  "release_id": "%s",\n' "${RELEASE_ID}"
    printf '  "overall": "%s",\n' "${overall}"
    printf '  "release_switch_decision": "%s",\n' "${decision}"
    printf '  "artifact_dir": "%s",\n' "${ARTIFACT_DIR}"
    printf '  "stages": [\n'
    for i in "${!STAGE_NAMES[@]}"; do
      printf '    {"name": "%s", "exit_code": %s, "status": "%s", "log": "%s"}' \
        "${STAGE_NAMES[$i]}" "${STAGE_CODES[$i]}" "${STAGE_STATUS[$i]}" "${STAGE_LOGS[$i]}"
      if [[ "$i" -lt "$((${#STAGE_NAMES[@]} - 1))" ]]; then
        printf ','
      fi
      printf '\n'
    done
    printf '  ]\n'
    printf '}\n'
  } > "${ARTIFACT_DIR}/summary.json"

  printf '%s\n' "${overall}" > "${ARTIFACT_DIR}/overall.txt"
  if [[ "${overall}" == "PASS" || "${overall}" == "PLANNED" ]]; then
    return 0
  fi
  return 1
}

package_artifacts() {
  local tarball="release-artifacts-${RELEASE_ID}.tar.gz"
  printf '%s\n' "${tarball}" > "${ARTIFACT_DIR}/artifact-tarball.txt"
  tar -czf "${tarball}" "${ARTIFACT_DIR}"
  echo "ARTIFACT=${tarball}"
}

capture_meta

run_step source_preflight preflight_source_tree

run_or_plan_step docker_preflight docker ps

if stage_succeeded source_preflight && stage_succeeded docker_preflight; then
  run_or_plan_step build_test_image \
    docker build -f Dockerfile.test -t "${TEST_IMAGE_TAG}" -t "${TEST_IMAGE_ALIAS}" .
else
  skip_step build_test_image "source_preflight or docker_preflight did not pass"
fi

if stage_succeeded build_test_image; then
  run_or_plan_step test_image_python \
    docker run --rm "${TEST_IMAGE_TAG}" python --version
else
  skip_step test_image_python "build_test_image did not pass"
fi

if stage_succeeded build_test_image; then
  run_or_plan_step ci_gate \
    docker run --rm \
      -v "${BASELINE_DIR}:/app/docs/current/status/baselines" \
      "${TEST_IMAGE_TAG}" \
      python scripts/run_ci.py --python python3 --keep-going --isolate-test-files \
        --coverage-fail-under "${COVERAGE_FAIL_UNDER}" \
        --coverage-xml docs/current/status/baselines/coverage.xml
else
  skip_step ci_gate "build_test_image did not pass"
fi

if stage_succeeded source_preflight && stage_succeeded docker_preflight; then
  run_or_plan_step build_runtime_image \
    docker build -t "${VERSIONED_RUNTIME_IMAGE_TAG}" -t "${RUNTIME_IMAGE_TAG}" -t "${RUNTIME_IMAGE_ALIAS}" .
else
  skip_step build_runtime_image "source_preflight or docker_preflight did not pass"
fi

if stage_succeeded build_test_image && runtime_image_ready; then
  run_or_plan_step container_smoke \
    docker run --rm --network host \
      -v /var/run/docker.sock:/var/run/docker.sock \
      "${TEST_IMAGE_TAG}" \
      python scripts/run_container_smoke.py \
        --image-tag "${RUNTIME_IMAGE_TAG}" \
        --port "${SMOKE_PORT}" \
        --skip-build
else
  skip_step container_smoke "build_test_image or build_runtime_image did not pass"
fi

if stage_succeeded build_test_image && runtime_image_ready; then
  run_or_plan_step api_acceptance api_acceptance
else
  skip_step api_acceptance "build_test_image or build_runtime_image did not pass"
fi

if stage_succeeded build_test_image && runtime_image_ready; then
  run_or_plan_step linux_validation_suite \
    docker run --rm --network host \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v "${BASELINE_DIR}:/app/docs/current/status/baselines" \
      -e OMNI_TEST_POSTGRES_DSN="${OMNI_TEST_POSTGRES_DSN:-}" \
      "${TEST_IMAGE_TAG}" \
      python scripts/run_linux_validation_suite.py \
        --python python3 \
        --keep-going \
        --container-image-tag "${RUNTIME_IMAGE_TAG}"
else
  skip_step linux_validation_suite "build_test_image or build_runtime_image did not pass"
fi

if stage_succeeded build_test_image && runtime_image_ready; then
  run_or_plan_step release_switch \
    docker run --rm --network host \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v "${BASELINE_DIR}:/app/docs/current/status/baselines" \
      -e OMNI_TEST_POSTGRES_DSN="${OMNI_TEST_POSTGRES_DSN:-}" \
      "${TEST_IMAGE_TAG}" \
      python scripts/run_release_switch_validation.py \
        --python python3 \
        --keep-going \
        --container-image-tag "${RUNTIME_IMAGE_TAG}"
else
  skip_step release_switch "build_test_image or build_runtime_image did not pass"
fi

copy_evidence
DECISION="$(read_release_decision)"
write_summary "${DECISION}"
SUMMARY_CODE=$?
package_artifacts

echo "SUMMARY=${ARTIFACT_DIR}/summary.tsv"
echo "DECISION=${DECISION}"
exit "${SUMMARY_CODE}"
