#!/usr/bin/env bash
set -euo pipefail

# Determine sidecar directory (where this script is located)
SIDECAR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
# Export Django settings module if set (for framework detection)
if [[ -n "${DJANGO_SETTINGS_MODULE:-}" ]]; then
  export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}"
fi
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SIDECAR_APP_LOG="${SIDECAR_APP_LOG:-${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-app.log}"

# Detect Python executable (prefer venv if available)
PYTHON_CMD="${PYTHON_CMD:-python3}"
if [[ -d "${REPO_PATH}/.venv" ]]; then
  VENV_PYTHON="${REPO_PATH}/.venv/bin/python"
  if [[ -f "${VENV_PYTHON}" ]]; then
    PYTHON_CMD="${VENV_PYTHON}"
    echo "[sidecar] using venv Python: ${PYTHON_CMD}"
  fi
elif [[ -d "${REPO_PATH}/venv" ]]; then
  VENV_PYTHON="${REPO_PATH}/venv/bin/python"
  if [[ -f "${VENV_PYTHON}" ]]; then
    PYTHON_CMD="${VENV_PYTHON}"
    echo "[sidecar] using venv Python: ${PYTHON_CMD}"
  fi
fi

# Detect framework type for environment setup
FRAMEWORK_TYPE="${FRAMEWORK_TYPE:-}"
if [[ -z "${FRAMEWORK_TYPE}" ]]; then
  # FastAPI detection
  if find "${REPO_PATH}" -maxdepth 3 -name "main.py" -o -name "app.py" | xargs grep -l "from fastapi import\|FastAPI(" 2>/dev/null | head -1 | grep -q .; then
    FRAMEWORK_TYPE="fastapi"
    echo "[sidecar] detected framework: FastAPI"
  # Django detection
  elif [[ -f "${REPO_PATH}/manage.py" ]] || find "${REPO_PATH}" -maxdepth 2 -name "urls.py" -type f 2>/dev/null | grep -q .; then
    FRAMEWORK_TYPE="django"
    echo "[sidecar] detected framework: Django"
    # Set Django settings module if not already set
    if [[ -z "${DJANGO_SETTINGS_MODULE:-}" ]]; then
      # Try to detect Django settings module
      if [[ -f "${REPO_PATH}/manage.py" ]]; then
        SETTINGS_MODULE=$(grep -oP "DJANGO_SETTINGS_MODULE\s*=\s*['\"]([^'\"]+)['\"]" "${REPO_PATH}/manage.py" 2>/dev/null | head -1 | sed "s/.*['\"]\([^'\"]*\)['\"].*/\1/" || echo "")
        if [[ -n "${SETTINGS_MODULE}" ]]; then
          export DJANGO_SETTINGS_MODULE="${SETTINGS_MODULE}"
          echo "[sidecar] auto-detected DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}"
        fi
      fi
    else
      export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}"
      echo "[sidecar] using DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}"
    fi
  # Add other framework detection here (Pyramid, etc.)
  fi
fi

if [[ -z "${SIDECAR_SOURCE_DIRS}" ]]; then
  if [[ -d "${REPO_PATH}/src" ]]; then
    SIDECAR_SOURCE_DIRS="${REPO_PATH}/src"
  elif [[ -d "${REPO_PATH}/lib" ]]; then
    SIDECAR_SOURCE_DIRS="${REPO_PATH}/lib"
  elif [[ -d "${REPO_PATH}/backend/app" ]]; then
    # FastAPI apps often have backend/app structure
    SIDECAR_SOURCE_DIRS="${REPO_PATH}/backend/app"
  else
    SIDECAR_SOURCE_DIRS="${REPO_PATH}"
  fi
fi

# Filter out test directories from CrossHair source analysis
# CrossHair tries to import everything, including test files that may require pytest
_filter_crosshair_dirs() {
  local dirs=("$@")
  local filtered=()
  for dir in "${dirs[@]}"; do
    # Skip common test directory patterns
    if [[ "$dir" == *"/test"* ]] || [[ "$dir" == *"/tests"* ]] || [[ "$dir" == *"/test_"* ]] || [[ "$dir" == *"/__pycache__"* ]]; then
      continue
    fi
    # Check if directory contains test files
    if find "$dir" -maxdepth 2 -name "test_*.py" -o -name "*_test.py" -o -name "conftest.py" 2>/dev/null | grep -q .; then
      # Directory contains test files, skip it
      continue
    fi
    filtered+=("$dir")
  done
  echo "${filtered[@]}"
}

# Convert source directory paths to Python module names for CrossHair
# CrossHair expects module names (e.g., "sqlalchemy") not paths (e.g., "lib/sqlalchemy")
# This function extracts the module name and ensures PYTHONPATH includes the parent directory
_path_to_module() {
  local source_path="$1"
  local repo_path="${2:-${REPO_PATH}}"
  
  # Remove trailing slash
  source_path="${source_path%/}"
  
  # If it's an absolute path, make it relative to repo
  if [[ "$source_path" == /* ]]; then
    source_path="${source_path#${repo_path}/}"
  fi
  
  # Handle common patterns: lib/pkg, src/pkg, backend/app, pkg
  # Extract the module name (last component that's a valid Python package)
  local module_name=""
  local parent_dir=""
  
  if [[ "$source_path" == *"/"* ]]; then
    # Path has directory structure (e.g., lib/sqlalchemy, src/mypackage)
    parent_dir="${source_path%/*}"  # Everything before last /
    module_name="${source_path##*/}"  # Last component
    
    # Check if the module directory has __init__.py (is a package)
    local full_module_path="${repo_path}/${source_path}"
    if [[ -f "${full_module_path}/__init__.py" ]]; then
      # It's a package - return module name and parent dir
      echo "${module_name}|${repo_path}/${parent_dir}"
      return 0
    fi
    
    # Check subdirectories for packages (e.g., lib/sqlalchemy where sqlalchemy is the package)
    for subdir in "${full_module_path}"/*; do
      if [[ -d "$subdir" ]] && [[ -f "${subdir}/__init__.py" ]]; then
        # Found a package subdirectory
        echo "$(basename "$subdir")|${full_module_path}"
        return 0
      fi
    done
  fi
  
  # No directory structure or no package found - use the path as-is
  # This handles cases like "mypackage" where PYTHONPATH is already set correctly
  echo "${source_path}|"
}

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

# AI Enrichment Step (BEFORE contract population)
# This is where AI should add reasoning/value to strengthen contracts
# TODO: Integrate AI enrichment here to:
#   - Analyze code (FastAPI routes, Pydantic models, validation logic)
#   - Extract Pydantic model schemas
#   - Add validation rules (minLength, maxLength, pattern, etc.)
#   - Add required fields and type constraints
#   - Update OpenAPI contract schemas with enriched details
# For now, this step is manual (Phase 2 enrichment) but should be automated in sidecar
ENRICH_CONTRACTS="${ENRICH_CONTRACTS:-0}"
if [[ "${ENRICH_CONTRACTS}" == "1" ]] && [[ -d "${CONTRACTS_DIR}" ]]; then
  echo "[sidecar] AI enrichment (strengthen contracts with reasoning)..."
  echo "[sidecar] TODO: Integrate AI enrichment to analyze code and strengthen contract schemas"
  echo "[sidecar] For now, using existing contracts (may be weak from Phase 1)"
  # Future: Call AI enrichment service/command here
  # Future: AI analyzes code and updates contract schemas with:
  #   - Pydantic model schemas
  #   - Validation rules
  #   - Required fields
  #   - Type constraints
fi

# Populate contracts with framework-specific patterns (Django, FastAPI, etc.)
POPULATE_CONTRACTS="${POPULATE_CONTRACTS:-1}"
if [[ "${POPULATE_CONTRACTS}" == "1" ]] && [[ -d "${CONTRACTS_DIR}" ]]; then
  if [[ "${FRAMEWORK_TYPE}" == "django" ]] || [[ "${FRAMEWORK_TYPE}" == "fastapi" ]]; then
    echo "[sidecar] populate contracts (${FRAMEWORK_TYPE} routes)..."
    run_and_log "${TIMEOUT_CROSSHAIR}" \
      "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-populate-contracts.log" \
      "${PYTHON_CMD}" "${SIDECAR_DIR}/populate_contracts.py" \
      --contracts "${CONTRACTS_DIR}" \
      --repo "${REPO_PATH}" \
      --bindings "${BINDINGS_PATH}" \
      --framework "${FRAMEWORK_TYPE}" \
      || echo "[sidecar] warning: contract population failed (continuing anyway)"
  else
    # For non-Django projects, just resolve schema references
    echo "[sidecar] resolve contract schema references..."
    run_and_log "${TIMEOUT_CROSSHAIR}" \
      "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-resolve-schemas.log" \
      "${PYTHON_CMD}" "${SIDECAR_DIR}/populate_contracts.py" \
      --contracts "${CONTRACTS_DIR}" \
      --resolve-schemas-only \
      || echo "[sidecar] warning: schema resolution failed (continuing anyway)"
  fi
fi

if [[ "${GENERATE_HARNESS}" == "1" ]]; then
  if [[ -d "${CONTRACTS_DIR}" ]]; then
    if [[ -z "${FEATURES_DIR}" ]]; then
      FEATURES_DIR="${CONTRACTS_DIR}/../features"
    fi
    echo "[sidecar] generate harness..."
    run_and_log "${TIMEOUT_CROSSHAIR}" \
      "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-harness.log" \
      "${PYTHON_CMD}" "${SIDECAR_DIR}/generate_harness.py" \
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

if [[ "${RUN_BASEDPYRIGHT}" == "1" ]]; then
  BASEDPYRIGHT_CMD="basedpyright"
  if [[ -f "${PYTHON_CMD}" ]] && "${PYTHON_CMD}" -m basedpyright --version >/dev/null 2>&1; then
    BASEDPYRIGHT_CMD="${PYTHON_CMD} -m basedpyright"
  elif ! command -v basedpyright >/dev/null 2>&1; then
    echo "[sidecar] basedpyright skipped (not available)"
  else
    echo "[sidecar] basedpyright..."
    run_and_log "${TIMEOUT_BASEDPYRIGHT}" \
      "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-basedpyright.log" \
      ${BASEDPYRIGHT_CMD} ${SIDECAR_SOURCE_DIRS}
  fi
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

  # Case A: Analyze source code directly (for existing decorators: beartype, icontract, etc.)
  # This catches contracts that are already in the source code (e.g., SpecFact CLI dogfooding)
  # Skip for FastAPI apps - they typically don't have decorators and require dependencies
  if [[ "${FRAMEWORK_TYPE}" == "fastapi" ]]; then
    echo "[sidecar] crosshair (source code - existing decorators)... skipped (FastAPI apps typically don't have decorators)"
  else
    echo "[sidecar] crosshair (source code - existing decorators)..."
    
    # Filter out test directories to avoid importing test files that require pytest
    CROSSHAIR_SOURCE_DIRS_ARRAY=(${SIDECAR_SOURCE_DIRS})
    CROSSHAIR_FILTERED_DIRS=$(_filter_crosshair_dirs "${CROSSHAIR_SOURCE_DIRS_ARRAY[@]}")
    
    if [[ -z "${CROSSHAIR_FILTERED_DIRS}" ]]; then
      echo "[sidecar] warning: all source directories filtered out (contain tests), skipping source code analysis"
    else
      # Convert source paths to module names for CrossHair
      # CrossHair expects module names (e.g., "sqlalchemy") not paths (e.g., "lib/sqlalchemy")
      CROSSHAIR_MODULES=""
      CROSSHAIR_EXTRA_PYTHONPATH=""
      for src_dir in ${CROSSHAIR_FILTERED_DIRS}; do
        MODULE_INFO=$(_path_to_module "$src_dir" "${REPO_PATH}")
        MODULE_NAME="${MODULE_INFO%%|*}"
        MODULE_PARENT="${MODULE_INFO##*|}"
        
        if [[ -n "$MODULE_NAME" ]]; then
          CROSSHAIR_MODULES="${CROSSHAIR_MODULES} ${MODULE_NAME}"
          if [[ -n "$MODULE_PARENT" ]] && [[ ":${CROSSHAIR_EXTRA_PYTHONPATH}:" != *":${MODULE_PARENT}:"* ]]; then
            CROSSHAIR_EXTRA_PYTHONPATH="${CROSSHAIR_EXTRA_PYTHONPATH}:${MODULE_PARENT}"
          fi
        fi
      done
      CROSSHAIR_MODULES="${CROSSHAIR_MODULES# }"  # Trim leading space
      CROSSHAIR_EXTRA_PYTHONPATH="${CROSSHAIR_EXTRA_PYTHONPATH#:}"  # Trim leading colon
      
      if [[ -z "${CROSSHAIR_MODULES}" ]]; then
        echo "[sidecar] warning: could not convert source directories to modules, skipping source code analysis"
      else
        echo "[sidecar] analyzing modules: ${CROSSHAIR_MODULES}"
        if [[ -n "${CROSSHAIR_EXTRA_PYTHONPATH}" ]]; then
          echo "[sidecar] extra PYTHONPATH: ${CROSSHAIR_EXTRA_PYTHONPATH}"
        fi
        
        # Build PYTHONPATH for CrossHair (include extra paths for module resolution)
        CROSSHAIR_PYTHONPATH="${PYTHONPATH:-}"
        if [[ -n "${CROSSHAIR_EXTRA_PYTHONPATH}" ]]; then
          CROSSHAIR_PYTHONPATH="${CROSSHAIR_EXTRA_PYTHONPATH}:${CROSSHAIR_PYTHONPATH}"
        fi
        
        if [[ "${FRAMEWORK_TYPE}" == "django" ]]; then
          # Use Django-aware wrapper for source code analysis
          CROSSHAIR_WRAPPER="${SIDECAR_DIR}/../frameworks/django/crosshair_django_wrapper.py"
          if [[ -f "${CROSSHAIR_WRAPPER}" ]]; then
            echo "[sidecar] using Django-aware CrossHair wrapper for source analysis"
            # Export environment variables for Django initialization
            CROSSHAIR_ENV=""
            if [[ -n "${DJANGO_SETTINGS_MODULE:-}" ]]; then
              CROSSHAIR_ENV="DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} "
            fi
            if [[ -n "${REPO_PATH:-}" ]]; then
              CROSSHAIR_ENV="${CROSSHAIR_ENV}REPO_PATH=${REPO_PATH} "
            fi
            CROSSHAIR_ENV="${CROSSHAIR_ENV}PYTHONPATH=${CROSSHAIR_PYTHONPATH} "
            run_and_log "${TIMEOUT_CROSSHAIR}" \
              "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-crosshair-source.log" \
              env ${CROSSHAIR_ENV}"${PYTHON_CMD}" "${CROSSHAIR_WRAPPER}" check "${CROSSHAIR_ARGS[@]}" ${CROSSHAIR_MODULES}
          else
            echo "[sidecar] warning: Django wrapper not found, using standard CrossHair (may fail)"
            run_and_log "${TIMEOUT_CROSSHAIR}" \
              "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-crosshair-source.log" \
              env PYTHONPATH="${CROSSHAIR_PYTHONPATH}" "${PYTHON_CMD}" -m crosshair check "${CROSSHAIR_ARGS[@]}" ${CROSSHAIR_MODULES}
          fi
        else
          # Standard CrossHair for non-Django projects
          run_and_log "${TIMEOUT_CROSSHAIR}" \
            "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-crosshair-source.log" \
            env PYTHONPATH="${CROSSHAIR_PYTHONPATH}" "${PYTHON_CMD}" -m crosshair check "${CROSSHAIR_ARGS[@]}" ${CROSSHAIR_MODULES}
        fi
      fi
    fi
  fi

  # Case B: Analyze harness (for contracts added via harness generation)
  # This catches contracts added externally via harness_contracts.py for code without decorators
  # This is the primary analysis method for frameworks without decorators (Django, etc.)
  if [[ -f "${HARNESS_PATH}" ]]; then
    echo "[sidecar] crosshair (harness - external contracts)..."
    
    # Build PYTHONPATH for harness analysis:
    # 1. Sidecar directory (for harness imports like 'common.adapters')
    # 2. Original PYTHONPATH (for repo modules)
    HARNESS_DIR="$(cd "$(dirname "${HARNESS_PATH}")" && pwd)"
    HARNESS_FILE="$(basename "${HARNESS_PATH}")"
    HARNESS_MODULE="${HARNESS_FILE%.py}"  # Remove .py extension
    
    # Build PYTHONPATH: sidecar dir + original PYTHONPATH
    HARNESS_PYTHONPATH="${HARNESS_DIR}"
    if [[ -n "${PYTHONPATH:-}" ]]; then
      HARNESS_PYTHONPATH="${HARNESS_PYTHONPATH}:${PYTHONPATH}"
    fi
    
    # Export environment variables for CrossHair subprocess
    CROSSHAIR_ENV="PYTHONPATH=${HARNESS_PYTHONPATH} "
    if [[ -n "${DJANGO_SETTINGS_MODULE:-}" ]]; then
      CROSSHAIR_ENV="${CROSSHAIR_ENV}DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} "
    fi
    if [[ -n "${REPO_PATH:-}" ]]; then
      CROSSHAIR_ENV="${CROSSHAIR_ENV}REPO_PATH=${REPO_PATH} "
    fi
    
    # Change to harness directory to ensure valid module name (avoids hyphenated directory names in module path)
    run_and_log "${TIMEOUT_CROSSHAIR}" \
      "${SIDECAR_REPORTS_DIR}/${TIMESTAMP}-crosshair-harness.log" \
      bash -c "cd '${HARNESS_DIR}' && env ${CROSSHAIR_ENV}${PYTHON_CMD} -m crosshair check ${CROSSHAIR_ARGS[*]} ${HARNESS_MODULE}"
  else
    echo "[sidecar] crosshair harness skipped (${HARNESS_PATH} not found)"
  fi
fi
