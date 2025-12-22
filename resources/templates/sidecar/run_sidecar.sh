#!/usr/bin/env bash
set -euo pipefail

if [[ -f ".env" ]]; then
  set -a
  . ./.env
  set +a
fi

REPO_PATH="${REPO_PATH:-${1:-}}"
BUNDLE_NAME="${BUNDLE_NAME:-${2:-}}"
SEMGREP_CONFIG="${SEMGREP_CONFIG:-}"
REPO_PYTHONPATH="${REPO_PYTHONPATH:-${REPO_PATH}/src:${REPO_PATH}}"
SIDECAR_SOURCE_DIRS="${SIDECAR_SOURCE_DIRS:-}"
RUN_SEMGREP="${RUN_SEMGREP:-1}"
RUN_BASEDPYRIGHT="${RUN_BASEDPYRIGHT:-0}"
RUN_SPECMATIC="${RUN_SPECMATIC:-1}"
RUN_CROSSHAIR="${RUN_CROSSHAIR:-1}"
GENERATE_HARNESS="${GENERATE_HARNESS:-1}"
TIMEOUT_SEMGREP="${TIMEOUT_SEMGREP:-60}"
TIMEOUT_BASEDPYRIGHT="${TIMEOUT_BASEDPYRIGHT:-60}"
TIMEOUT_SPECMATIC="${TIMEOUT_SPECMATIC:-60}"
TIMEOUT_CROSSHAIR="${TIMEOUT_CROSSHAIR:-60}"
HARNESS_PATH="${HARNESS_PATH:-harness_contracts.py}"
INPUTS_PATH="${INPUTS_PATH:-inputs.json}"
SIDECAR_REPORTS_DIR="${SIDECAR_REPORTS_DIR:-${REPO_PATH}/.specfact/projects/${BUNDLE_NAME}/reports/sidecar}"
BINDINGS_PATH="${BINDINGS_PATH:-bindings.yaml}"
FEATURES_DIR="${FEATURES_DIR:-}"
SPECMATIC_CMD="${SPECMATIC_CMD:-}"
SPECMATIC_JAR="${SPECMATIC_JAR:-}"
SPECMATIC_CONFIG="${SPECMATIC_CONFIG:-}"
SPECMATIC_TEST_BASE_URL="${SPECMATIC_TEST_BASE_URL:-}"
SPECMATIC_HOST="${SPECMATIC_HOST:-}"
SPECMATIC_PORT="${SPECMATIC_PORT:-}"
SPECMATIC_TIMEOUT="${SPECMATIC_TIMEOUT:-}"
SPECMATIC_AUTO_STUB="${SPECMATIC_AUTO_STUB:-1}"
SPECMATIC_STUB_HOST="${SPECMATIC_STUB_HOST:-127.0.0.1}"
SPECMATIC_STUB_PORT="${SPECMATIC_STUB_PORT:-19000}"
SPECMATIC_STUB_WAIT="${SPECMATIC_STUB_WAIT:-15}"
SIDECAR_APP_CMD="${SIDECAR_APP_CMD:-}"
SIDECAR_APP_HOST="${SIDECAR_APP_HOST:-127.0.0.1}"
SIDECAR_APP_PORT="${SIDECAR_APP_PORT:-}"
SIDECAR_APP_WAIT="${SIDECAR_APP_WAIT:-15}"
SIDECAR_APP_LOG="${SIDECAR_APP_LOG:-}"
CROSSHAIR_VERBOSE="${CROSSHAIR_VERBOSE:-0}"
CROSSHAIR_REPORT_ALL="${CROSSHAIR_REPORT_ALL:-0}"
CROSSHAIR_REPORT_VERBOSE="${CROSSHAIR_REPORT_VERBOSE:-0}"
CROSSHAIR_MAX_UNINTERESTING_ITERATIONS="${CROSSHAIR_MAX_UNINTERESTING_ITERATIONS:-}"
CROSSHAIR_PER_PATH_TIMEOUT="${CROSSHAIR_PER_PATH_TIMEOUT:-}"
CROSSHAIR_PER_CONDITION_TIMEOUT="${CROSSHAIR_PER_CONDITION_TIMEOUT:-}"
CROSSHAIR_ANALYSIS_KIND="${CROSSHAIR_ANALYSIS_KIND:-}"
CROSSHAIR_EXTRA_PLUGIN="${CROSSHAIR_EXTRA_PLUGIN:-}"

if [[ -z "${REPO_PATH}" || -z "${BUNDLE_NAME}" ]]; then
  echo "Usage: REPO_PATH=/path/to/repo BUNDLE_NAME=bundle ./run_sidecar.sh"
  echo "  Optional: SEMGREP_CONFIG=/path/to/semgrep.yml"
  echo "  Optional: REPO_PYTHONPATH=/path/to/repo/src:/path/to/repo"
  exit 1
fi

CONTRACTS_DIR="${REPO_PATH}/.specfact/projects/${BUNDLE_NAME}/contracts"
export PYTHONPATH="${REPO_PYTHONPATH}:${PYTHONPATH:-}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SIDECAR_APP_LOG="${SIDECAR_APP_LOG:-${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-app.log}"

if [[ -z "${SIDECAR_SOURCE_DIRS}" ]]; then
  if [[ -d "${REPO_PATH}/src" ]]; then
    SIDECAR_SOURCE_DIRS="${REPO_PATH}/src"
  elif [[ -d "${REPO_PATH}/lib" ]]; then
    SIDECAR_SOURCE_DIRS="${REPO_PATH}/lib"
  else
    SIDECAR_SOURCE_DIRS="${REPO_PATH}"
  fi
fi

run_with_timeout() {
  local timeout_secs="$1"
  shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "${timeout_secs}" "$@" || true
  else
    "$@" || true
  fi
}

run_and_log() {
  local timeout_secs="$1"
  local log_file="$2"
  shift 2
  mkdir -p "$(dirname "${log_file}")"
  if command -v timeout >/dev/null 2>&1; then
    timeout "${timeout_secs}" "$@" 2>&1 | tee "${log_file}" || true
  else
    "$@" 2>&1 | tee "${log_file}" || true
  fi
}

wait_for_port() {
  local host="$1"
  local port="$2"
  local timeout_secs="$3"
  local start_ts
  start_ts="$(date +%s)"
  while true; do
    if (echo >"/dev/tcp/${host}/${port}") >/dev/null 2>&1; then
      return 0
    fi
    if (( $(date +%s) - start_ts >= timeout_secs )); then
      return 1
    fi
    sleep 0.2
  done
}

resolve_specmatic_cmd() {
  SPEC_CMD=()
  SPEC_CMD_LABEL=""
  if [[ -n "${SPECMATIC_CMD}" ]]; then
    read -r -a SPEC_CMD <<< "${SPECMATIC_CMD}"
    SPEC_CMD_LABEL="cmd"
  elif [[ -n "${SPECMATIC_JAR}" && -f "${SPECMATIC_JAR}" ]]; then
    SPEC_CMD=(java -jar "${SPECMATIC_JAR}")
    SPEC_CMD_LABEL="jar"
  elif command -v specmatic >/dev/null 2>&1; then
    SPEC_CMD=(specmatic)
    SPEC_CMD_LABEL="cli"
  elif command -v npx >/dev/null 2>&1; then
    SPEC_CMD=(npx --yes specmatic)
    SPEC_CMD_LABEL="npx"
  elif python - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("specmatic.cli") else 1)
PY
  then
    SPEC_CMD=(python -m specmatic.cli)
    SPEC_CMD_LABEL="module"
  elif python - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("specmatic.__main__") else 1)
PY
  then
    SPEC_CMD=(python -m specmatic)
    SPEC_CMD_LABEL="module-main"
  fi
}

echo "[sidecar] repo: ${REPO_PATH}"
echo "[sidecar] bundle: ${BUNDLE_NAME}"
echo "[sidecar] contracts: ${CONTRACTS_DIR}"
echo "[sidecar] sources: ${SIDECAR_SOURCE_DIRS}"
echo "[sidecar] reports: ${SIDECAR_REPORTS_DIR}"

if [[ "${GENERATE_HARNESS}" == "1" ]]; then
  if [[ -d "${CONTRACTS_DIR}" ]]; then
    if [[ -z "${FEATURES_DIR}" ]]; then
      FEATURES_DIR="${CONTRACTS_DIR}/../features"
    fi
    echo "[sidecar] generate harness..."
    run_and_log "${TIMEOUT_CROSSHAIR}" \
      "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-harness.log" \
      python generate_harness.py \
      --contracts "${CONTRACTS_DIR}" \
      --output "${HARNESS_PATH}" \
      --inputs "${INPUTS_PATH}" \
      --features "${FEATURES_DIR}" \
      --bindings "${BINDINGS_PATH}"
  fi
fi

if [[ "${RUN_SEMGREP}" == "1" && -n "${SEMGREP_CONFIG}" && -f "${SEMGREP_CONFIG}" ]]; then
  echo "[sidecar] semgrep..."
  run_and_log "${TIMEOUT_SEMGREP}" \
    "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-semgrep.log" \
    semgrep --config "${SEMGREP_CONFIG}" ${SIDECAR_SOURCE_DIRS}
fi

if [[ "${RUN_BASEDPYRIGHT}" == "1" ]] && command -v basedpyright >/dev/null 2>&1; then
  echo "[sidecar] basedpyright..."
  run_and_log "${TIMEOUT_BASEDPYRIGHT}" \
    "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-basedpyright.log" \
    basedpyright ${SIDECAR_SOURCE_DIRS}
fi

if [[ "${RUN_SPECMATIC}" == "1" && -d "${CONTRACTS_DIR}" ]]; then
  mapfile -t SPEC_CONTRACTS < <(
    find "${CONTRACTS_DIR}" -maxdepth 1 -type f \( \
      -name "*.openapi.yaml" -o -name "*.openapi.yml" -o -name "*.openapi.json" \
    \) | sort
  )
  resolve_specmatic_cmd
  if [[ "${#SPEC_CONTRACTS[@]}" -eq 0 && -z "${SPECMATIC_CONFIG}" ]]; then
    echo "[sidecar] specmatic skipped (no contracts found)."
  elif [[ "${#SPEC_CMD[@]}" -eq 0 ]]; then
    echo "[sidecar] specmatic not available (set SPECMATIC_CMD or SPECMATIC_JAR)."
  else
    SPEC_ARGS=()
    if [[ -n "${SPECMATIC_CONFIG}" ]]; then
      SPEC_ARGS+=(--config "${SPECMATIC_CONFIG}")
    fi
    if [[ -n "${SPECMATIC_TEST_BASE_URL}" ]]; then
      SPEC_ARGS+=(--testBaseURL "${SPECMATIC_TEST_BASE_URL}")
    fi
    if [[ -n "${SPECMATIC_HOST}" ]]; then
      SPEC_ARGS+=(--host "${SPECMATIC_HOST}")
    fi
    if [[ -n "${SPECMATIC_PORT}" ]]; then
      SPEC_ARGS+=(--port "${SPECMATIC_PORT}")
    fi
    if [[ -n "${SPECMATIC_TIMEOUT}" ]]; then
      SPEC_ARGS+=(--timeout "${SPECMATIC_TIMEOUT}")
    fi

    SIDECAR_APP_PID=""
    SIDECAR_STUB_PID=""

    if [[ -n "${SIDECAR_APP_CMD}" ]]; then
      echo "[sidecar] starting app: ${SIDECAR_APP_CMD}"
      mkdir -p "$(dirname "${SIDECAR_APP_LOG}")"
      bash -c "${SIDECAR_APP_CMD}" >"${SIDECAR_APP_LOG}" 2>&1 &
      SIDECAR_APP_PID=$!
      if [[ -n "${SIDECAR_APP_PORT}" ]]; then
        if ! wait_for_port "${SIDECAR_APP_HOST}" "${SIDECAR_APP_PORT}" "${SIDECAR_APP_WAIT}"; then
          echo "[sidecar] app did not become ready on ${SIDECAR_APP_HOST}:${SIDECAR_APP_PORT}"
        fi
      fi
      if [[ -z "${SPECMATIC_TEST_BASE_URL}" && -n "${SIDECAR_APP_PORT}" ]]; then
        SPECMATIC_TEST_BASE_URL="http://${SIDECAR_APP_HOST}:${SIDECAR_APP_PORT}"
        SPEC_ARGS+=(--testBaseURL "${SPECMATIC_TEST_BASE_URL}")
      fi
    elif [[ "${SPECMATIC_AUTO_STUB}" == "1" && -z "${SPECMATIC_TEST_BASE_URL}" && -z "${SPECMATIC_HOST}" && -z "${SPECMATIC_PORT}" && -z "${SPECMATIC_CONFIG}" ]]; then
      echo "[sidecar] specmatic stub (${SPEC_CMD_LABEL})..."
      STUB_LOG="${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-specmatic-stub.log"
      mkdir -p "$(dirname "${STUB_LOG}")"
      "${SPEC_CMD[@]}" stub --host "${SPECMATIC_STUB_HOST}" --port "${SPECMATIC_STUB_PORT}" "${SPEC_CONTRACTS[@]}" \
        >"${STUB_LOG}" 2>&1 &
      SIDECAR_STUB_PID=$!
      if wait_for_port "${SPECMATIC_STUB_HOST}" "${SPECMATIC_STUB_PORT}" "${SPECMATIC_STUB_WAIT}"; then
        SPECMATIC_TEST_BASE_URL="http://${SPECMATIC_STUB_HOST}:${SPECMATIC_STUB_PORT}"
        SPEC_ARGS+=(--testBaseURL "${SPECMATIC_TEST_BASE_URL}")
      else
        echo "[sidecar] specmatic stub did not start on ${SPECMATIC_STUB_HOST}:${SPECMATIC_STUB_PORT}"
      fi
    fi

    echo "[sidecar] specmatic (${SPEC_CMD_LABEL})..."
    run_and_log "${TIMEOUT_SPECMATIC}" \
      "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-specmatic.log" \
      "${SPEC_CMD[@]}" test "${SPEC_ARGS[@]}" "${SPEC_CONTRACTS[@]}"

    if [[ -n "${SIDECAR_STUB_PID}" ]]; then
      kill "${SIDECAR_STUB_PID}" >/dev/null 2>&1 || true
    fi
    if [[ -n "${SIDECAR_APP_PID}" ]]; then
      kill "${SIDECAR_APP_PID}" >/dev/null 2>&1 || true
    fi
  fi
fi

if [[ "${RUN_CROSSHAIR}" == "1" ]] && command -v crosshair >/dev/null 2>&1; then
  CROSSHAIR_ARGS=()
  if [[ "${CROSSHAIR_VERBOSE}" == "1" ]]; then
    CROSSHAIR_ARGS+=(--verbose)
  fi
  if [[ "${CROSSHAIR_REPORT_ALL}" == "1" ]]; then
    CROSSHAIR_ARGS+=(--report_all)
  fi
  if [[ "${CROSSHAIR_REPORT_VERBOSE}" == "1" ]]; then
    CROSSHAIR_ARGS+=(--report_verbose)
  fi
  if [[ -n "${CROSSHAIR_MAX_UNINTERESTING_ITERATIONS}" ]]; then
    CROSSHAIR_ARGS+=(--max_uninteresting_iterations "${CROSSHAIR_MAX_UNINTERESTING_ITERATIONS}")
  fi
  if [[ -n "${CROSSHAIR_PER_PATH_TIMEOUT}" ]]; then
    CROSSHAIR_ARGS+=(--per_path_timeout "${CROSSHAIR_PER_PATH_TIMEOUT}")
  fi
  if [[ -n "${CROSSHAIR_PER_CONDITION_TIMEOUT}" ]]; then
    CROSSHAIR_ARGS+=(--per_condition_timeout "${CROSSHAIR_PER_CONDITION_TIMEOUT}")
  fi
  if [[ -n "${CROSSHAIR_ANALYSIS_KIND}" ]]; then
    CROSSHAIR_ARGS+=(--analysis_kind "${CROSSHAIR_ANALYSIS_KIND}")
  fi
  if [[ -n "${CROSSHAIR_EXTRA_PLUGIN}" ]]; then
    CROSSHAIR_ARGS+=(--extra_plugin "${CROSSHAIR_EXTRA_PLUGIN}")
  fi
  echo "[sidecar] crosshair (harness)..."
  run_and_log "${TIMEOUT_CROSSHAIR}" \
    "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-crosshair.log" \
    python -m crosshair check "${CROSSHAIR_ARGS[@]}" "${HARNESS_PATH}"
fi
