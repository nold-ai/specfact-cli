#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="${SCRIPT_DIR}"

TARGET_DIR="${1:-}"
REPO_PATH="${2:-}"
BUNDLE_NAME="${3:-}"

if [[ -z "${TARGET_DIR}" ]]; then
  echo "Usage: ${0} <target_dir> [repo_path] [bundle_name]"
  exit 1
fi

mkdir -p "${TARGET_DIR}"
cp -R "${TEMPLATE_DIR}/." "${TARGET_DIR}/"

if [[ -n "${REPO_PATH}" && -n "${BUNDLE_NAME}" ]]; then
  # Detect Python executable (prefer venv if available)
  PYTHON_CMD="python3"
  if [[ -d "${REPO_PATH}/.venv" ]] && [[ -f "${REPO_PATH}/.venv/bin/python" ]]; then
    PYTHON_CMD="${REPO_PATH}/.venv/bin/python"
  elif [[ -d "${REPO_PATH}/venv" ]] && [[ -f "${REPO_PATH}/venv/bin/python" ]]; then
    PYTHON_CMD="${REPO_PATH}/venv/bin/python"
  fi

  # Detect framework and set environment variables
  DJANGO_SETTINGS_MODULE=""
  if [[ -f "${REPO_PATH}/manage.py" ]] || find "${REPO_PATH}" -maxdepth 2 -name "urls.py" -type f 2>/dev/null | grep -q .; then
    # Django detected - try to extract settings module
    if [[ -f "${REPO_PATH}/manage.py" ]]; then
      # Try multiple patterns to extract Django settings module
      SETTINGS_MODULE=$(grep -oP "DJANGO_SETTINGS_MODULE\s*=\s*['\"]([^'\"]+)['\"]" "${REPO_PATH}/manage.py" 2>/dev/null | head -1 | sed "s/.*['\"]\([^'\"]*\)['\"].*/\1/" || echo "")
      # If not found, try to detect from project structure
      if [[ -z "${SETTINGS_MODULE}" ]]; then
        # Look for settings.py in common locations
        SETTINGS_FILE=$(find "${REPO_PATH}" -maxdepth 2 -name "settings.py" -type f 2>/dev/null | head -1)
        if [[ -n "${SETTINGS_FILE}" ]]; then
          # Extract module path (e.g., /path/to/djangogoat/settings.py -> djangogoat.settings)
          SETTINGS_DIR=$(dirname "${SETTINGS_FILE}" | sed "s|${REPO_PATH}/||" | sed "s|^\./||")
          if [[ -n "${SETTINGS_DIR}" ]]; then
            SETTINGS_MODULE="${SETTINGS_DIR//\//.}.settings"
          else
            # If settings.py is in repo root, try to detect project name from manage.py
            PROJECT_NAME=$(grep -oP "DJANGO_SETTINGS_MODULE\s*=\s*['\"]([^'\"]+)['\"]" "${REPO_PATH}/manage.py" 2>/dev/null | head -1 | sed "s/.*['\"]\([^'\"]*\)['\"].*/\1/" | cut -d. -f1 || echo "")
            if [[ -z "${PROJECT_NAME}" ]]; then
              # Fallback: use directory name
              PROJECT_NAME=$(basename "${REPO_PATH}")
            fi
            SETTINGS_MODULE="${PROJECT_NAME}.settings"
          fi
        fi
      fi
      if [[ -n "${SETTINGS_MODULE}" ]]; then
        DJANGO_SETTINGS_MODULE="${SETTINGS_MODULE}"
      fi
    fi
    # Default Django Python path includes venv if available
    # Find Python version-specific site-packages directory
    if [[ -d "${REPO_PATH}/.venv" ]]; then
      # Try to find actual Python version directory
      PYTHON_VERSION_DIR=$(find "${REPO_PATH}/.venv/lib" -maxdepth 1 -type d -name "python*" 2>/dev/null | head -1)
      if [[ -n "${PYTHON_VERSION_DIR}" ]] && [[ -d "${PYTHON_VERSION_DIR}/site-packages" ]]; then
        REPO_PYTHONPATH="${PYTHON_VERSION_DIR}/site-packages:${REPO_PATH}/src:${REPO_PATH}"
      else
        REPO_PYTHONPATH="${REPO_PATH}/.venv/lib/python*/site-packages:${REPO_PATH}/src:${REPO_PATH}"
      fi
    elif [[ -d "${REPO_PATH}/venv" ]]; then
      PYTHON_VERSION_DIR=$(find "${REPO_PATH}/venv/lib" -maxdepth 1 -type d -name "python*" 2>/dev/null | head -1)
      if [[ -n "${PYTHON_VERSION_DIR}" ]] && [[ -d "${PYTHON_VERSION_DIR}/site-packages" ]]; then
        REPO_PYTHONPATH="${PYTHON_VERSION_DIR}/site-packages:${REPO_PATH}/src:${REPO_PATH}"
      else
        REPO_PYTHONPATH="${REPO_PATH}/venv/lib/python*/site-packages:${REPO_PATH}/src:${REPO_PATH}"
      fi
    else
      REPO_PYTHONPATH="${REPO_PATH}/src:${REPO_PATH}"
    fi
  else
    REPO_PYTHONPATH="${REPO_PATH}/src:${REPO_PATH}"
  fi

  cat > "${TARGET_DIR}/.env" <<EOF
REPO_PATH=${REPO_PATH}
BUNDLE_NAME=${BUNDLE_NAME}
REPO_PYTHONPATH=${REPO_PYTHONPATH}
PYTHON_CMD=${PYTHON_CMD}
RUN_BASEDPYRIGHT=0
BINDINGS_PATH=bindings.yaml
FEATURES_DIR=${REPO_PATH}/.specfact/projects/${BUNDLE_NAME}/features
EOF

  # Add Django-specific settings if detected
  if [[ -n "${DJANGO_SETTINGS_MODULE}" ]]; then
    echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}" >> "${TARGET_DIR}/.env"
  fi

  echo "[sidecar-init] wrote ${TARGET_DIR}/.env"
  if [[ -n "${DJANGO_SETTINGS_MODULE}" ]]; then
    echo "[sidecar-init] detected Django framework, set DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}"
  fi
  if [[ "${PYTHON_CMD}" != "python3" ]]; then
    echo "[sidecar-init] detected venv, using ${PYTHON_CMD}"
  fi
fi

echo "[sidecar-init] sidecar templates copied to ${TARGET_DIR}"
