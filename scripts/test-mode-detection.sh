#!/bin/bash
# Test Mode Detection in Practice

set -e

echo "=== Testing Mode Detection ==="
echo

cd "$(dirname "$0")/.."

echo "1. Testing default mode (no overrides):"
hatch run python -c "
from specfact_cli.modes import detect_mode, OperationalMode
import os
os.environ.clear()
mode = detect_mode(explicit_mode=None)
print(f'   Default mode: {mode}')
"
echo

echo "2. Testing explicit CI/CD mode:"
hatch run python -c "
from specfact_cli.modes import detect_mode, OperationalMode
mode = detect_mode(explicit_mode=OperationalMode.CICD)
print(f'   Explicit CI/CD: {mode}')
"
echo

echo "3. Testing explicit CoPilot mode:"
hatch run python -c "
from specfact_cli.modes import detect_mode, OperationalMode
mode = detect_mode(explicit_mode=OperationalMode.COPILOT)
print(f'   Explicit CoPilot: {mode}')
"
echo

echo "4. Testing SPECFACT_MODE environment variable:"
SPECFACT_MODE=copilot hatch run python -c "
from specfact_cli.modes import detect_mode, OperationalMode
import os
mode = detect_mode(explicit_mode=None)
print(f'   SPECFACT_MODE=copilot: {mode}')
"
echo

echo "5. Testing COPILOT_API_URL detection:"
COPILOT_API_URL=https://api.copilot.com hatch run python -c "
from specfact_cli.modes import detect_mode, OperationalMode
import os
os.environ.pop('SPECFACT_MODE', None)
mode = detect_mode(explicit_mode=None)
print(f'   COPILOT_API_URL set: {mode}')
"
echo

echo "6. Testing IDE + CoPilot detection:"
VSCODE_PID=12345 COPILOT_ENABLED=true hatch run python -c "
from specfact_cli.modes import detect_mode, OperationalMode
import os
os.environ.pop('SPECFACT_MODE', None)
os.environ.pop('COPILOT_API_URL', None)
mode = detect_mode(explicit_mode=None)
print(f'   VS Code + CoPilot: {mode}')
"
echo

echo "7. Testing priority: explicit flag overrides environment:"
SPECFACT_MODE=copilot hatch run python -c "
from specfact_cli.modes import detect_mode, OperationalMode
import os
mode = detect_mode(explicit_mode=OperationalMode.CICD)
print(f'   Explicit flag overrides env var: {mode}')
"
echo

echo "=== All Tests Complete ==="

