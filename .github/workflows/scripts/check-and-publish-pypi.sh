#!/usr/bin/env bash
set -euo pipefail

# check-and-publish-pypi.sh
# Extracts version from pyproject.toml, compares with latest PyPI version,
# and publishes if the new version is greater.
# Usage: check-and-publish-pypi.sh

echo "🔍 Checking PyPI version..."

# Extract version from pyproject.toml
# Note: tomllib is part of Python 3.11+ standard library
# This project requires Python >= 3.11, so tomllib is always available
LOCAL_VERSION=$(python << 'PYTHON_SCRIPT'
import sys
import tomllib

try:
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)
        print(data['project']['version'])
except FileNotFoundError:
    print('Error: pyproject.toml not found', file=sys.stderr)
    sys.exit(1)
except KeyError as e:
    print(f'Error: Could not find version in pyproject.toml: {e}', file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT
)

echo "📦 Local version: $LOCAL_VERSION"

# Get latest PyPI version
echo "🌐 Querying PyPI for latest version..."
PYPI_VERSION=$(python << 'PYTHON_SCRIPT'
import json
import urllib.request
import sys

try:
    url = 'https://pypi.org/pypi/specfact-cli/json'
    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read())
        print(data['info']['version'])
except urllib.error.HTTPError as e:
    if e.code == 404:
        print('0.0.0')
    else:
        print(f'Error: HTTP {e.code}', file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f'Error querying PyPI: {e}', file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT
)

if [ -z "$PYPI_VERSION" ]; then
    echo "⚠️ Could not determine PyPI version, assuming first release"
    PYPI_VERSION="0.0.0"
fi

echo "📦 Latest PyPI version: $PYPI_VERSION"

# Compare versions using Python packaging
SHOULD_PUBLISH=$(python << PYTHON_SCRIPT
from packaging import version
import sys

local_ver = version.parse('$LOCAL_VERSION')
pypi_ver = version.parse('$PYPI_VERSION')

if local_ver > pypi_ver:
    print('true')
else:
    print('false')
    print(f'⚠️ Local version ({local_ver}) is not greater than PyPI version ({pypi_ver})', file=sys.stderr)
    print('Skipping PyPI publication.', file=sys.stderr)
PYTHON_SCRIPT
)

if [ "$SHOULD_PUBLISH" = "true" ]; then
    echo "✅ Version $LOCAL_VERSION is newer than PyPI version $PYPI_VERSION"
    echo "🚀 Publishing to PyPI..."
    
    # Build package
    echo "📦 Building package..."
    python -m pip install --upgrade build twine
    python -m build
    
    # Validate package
    echo "🔍 Validating package..."
    twine check dist/*
    
    # Publish to PyPI
    echo "📤 Publishing to PyPI..."
    if [ -z "${PYPI_API_TOKEN:-}" ]; then
        echo "❌ Error: PYPI_API_TOKEN secret is not set"
        exit 1
    fi
    twine upload dist/* \
        --username __token__ \
        --password "${PYPI_API_TOKEN}" \
        --non-interactive \
        --skip-existing
    
    echo "✅ Successfully published version $LOCAL_VERSION to PyPI"
    
    # Set output for workflow
    echo "published=true" >> $GITHUB_OUTPUT
    echo "version=$LOCAL_VERSION" >> $GITHUB_OUTPUT
else
    echo "⏭️ Skipping PyPI publication (version not newer)"
    echo "published=false" >> $GITHUB_OUTPUT
    echo "version=$LOCAL_VERSION" >> $GITHUB_OUTPUT
fi
