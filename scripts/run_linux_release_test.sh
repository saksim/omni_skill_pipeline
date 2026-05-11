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

mkdir -p "${LOG_DIR}" "${META_DIR}" "${BASELINE_DIR}"

STAGE_NAMES=()
STAGE_CODES=()
STAGE_LOGS=()

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

Outputs:
  release-artifacts/<RELEASE_ID>/logs/*.log
  release-artifacts/<RELEASE_ID>/logs/*.exit
  release-artifacts/<RELEASE_ID>/baselines/*
  release-artifacts/<RELEASE_ID>/summary.tsv
  release-artifacts/<RELEASE_ID>/summary.json
  release-artifacts-<RELEASE_ID>.tar.gz
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

record_stage() {
  local name="$1"
  local code="$2"
  local log_path="$3"
  STAGE_NAMES+=("${name}")
  STAGE_CODES+=("${code}")
  STAGE_LOGS+=("${log_path}")
  printf '%s\n' "${code}" > "${LOG_DIR}/${name}.exit"
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
  record_stage "${name}" "${code}" "${log_path}"
  return 0
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

  docker rm -f "${API_CONTAINER_NAME}" >/dev/null 2>&1 || true
  docker run --rm -d \
    --name "${API_CONTAINER_NAME}" \
    -p "${API_ACCEPTANCE_PORT}:8000" \
    --env-file "${runtime_env}" \
    -v "${API_DRAFTS_VOLUME}:/app/skills/drafts" \
    -v "${API_PUBLISHED_VOLUME}:/app/skills/published" \
    -v "${API_TMP_MEDIA_VOLUME}:/app/.tmp_omni_media" \
    "${RUNTIME_IMAGE_TAG}"

  poll_url "${base_url}/healthz" 30 1 || code=$?
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
  local i
  for i in "${!STAGE_NAMES[@]}"; do
    if [[ "${STAGE_CODES[$i]}" != "0" ]]; then
      overall="FAIL"
    fi
  done
  if [[ "${decision}" != "GO" ]]; then
    overall="FAIL"
  fi

  {
    printf 'stage\texit_code\tlog\n'
    for i in "${!STAGE_NAMES[@]}"; do
      printf '%s\t%s\t%s\n' "${STAGE_NAMES[$i]}" "${STAGE_CODES[$i]}" "${STAGE_LOGS[$i]}"
    done
    printf 'release_switch_decision\t%s\t%s\n' "${decision}" "${BASELINE_DIR}/e13-release-switch-decision-report.json"
    printf 'overall\t%s\t%s\n' "${overall}" "${ARTIFACT_DIR}"
  } > "${ARTIFACT_DIR}/summary.tsv"

  {
    printf '{\n'
    printf '  "release_id": "%s",\n' "${RELEASE_ID}"
    printf '  "overall": "%s",\n' "${overall}"
    printf '  "release_switch_decision": "%s",\n' "${decision}"
    printf '  "artifact_dir": "%s",\n' "${ARTIFACT_DIR}"
    printf '  "stages": [\n'
    for i in "${!STAGE_NAMES[@]}"; do
      printf '    {"name": "%s", "exit_code": %s, "log": "%s"}' \
        "${STAGE_NAMES[$i]}" "${STAGE_CODES[$i]}" "${STAGE_LOGS[$i]}"
      if [[ "$i" -lt "$((${#STAGE_NAMES[@]} - 1))" ]]; then
        printf ','
      fi
      printf '\n'
    done
    printf '  ]\n'
    printf '}\n'
  } > "${ARTIFACT_DIR}/summary.json"

  printf '%s\n' "${overall}" > "${ARTIFACT_DIR}/overall.txt"
  if [[ "${overall}" == "PASS" ]]; then
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

run_step docker_preflight docker ps

run_step build_test_image \
  docker build -f Dockerfile.test -t "${TEST_IMAGE_TAG}" -t "${TEST_IMAGE_ALIAS}" .

run_step test_image_python \
  docker run --rm "${TEST_IMAGE_TAG}" python --version

run_step ci_gate \
  docker run --rm \
    -v "${BASELINE_DIR}:/app/docs/current/status/baselines" \
    "${TEST_IMAGE_TAG}" \
    python scripts/run_ci.py --python python3 --keep-going --isolate-test-files \
      --coverage-fail-under "${COVERAGE_FAIL_UNDER}" \
      --coverage-xml docs/current/status/baselines/coverage.xml

run_step build_runtime_image \
  docker build -t "${VERSIONED_RUNTIME_IMAGE_TAG}" -t "${RUNTIME_IMAGE_TAG}" -t "${RUNTIME_IMAGE_ALIAS}" .

run_step container_smoke \
  docker run --rm --network host \
    -v /var/run/docker.sock:/var/run/docker.sock \
    "${TEST_IMAGE_TAG}" \
    python scripts/run_container_smoke.py \
      --image-tag "${RUNTIME_IMAGE_TAG}" \
      --port "${SMOKE_PORT}" \
      --skip-build

run_step api_acceptance api_acceptance

run_step linux_validation_suite \
  docker run --rm --network host \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${BASELINE_DIR}:/app/docs/current/status/baselines" \
    -e OMNI_TEST_POSTGRES_DSN="${OMNI_TEST_POSTGRES_DSN:-}" \
    "${TEST_IMAGE_TAG}" \
    python scripts/run_linux_validation_suite.py \
      --python python3 \
      --keep-going \
      --container-image-tag "${RUNTIME_IMAGE_TAG}"

run_step release_switch \
  docker run --rm --network host \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${BASELINE_DIR}:/app/docs/current/status/baselines" \
    -e OMNI_TEST_POSTGRES_DSN="${OMNI_TEST_POSTGRES_DSN:-}" \
    "${TEST_IMAGE_TAG}" \
    python scripts/run_release_switch_validation.py \
      --python python3 \
      --keep-going \
      --container-image-tag "${RUNTIME_IMAGE_TAG}"

copy_evidence
DECISION="$(read_release_decision)"
write_summary "${DECISION}"
SUMMARY_CODE=$?
package_artifacts

echo "SUMMARY=${ARTIFACT_DIR}/summary.tsv"
echo "DECISION=${DECISION}"
exit "${SUMMARY_CODE}"
