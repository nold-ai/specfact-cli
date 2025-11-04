# Testing Mode Detection and Command Routing

This guide shows how to test mode detection (Phase 3.1) and command routing (Phase 3.2) in practice.

## Quick Test Commands

**Note**: The CLI must be run through `hatch run` or installed first. Use `hatch run specfact` or install with `hatch build && pip install -e .`.

### 1. Test Explicit Mode Flags

```bash
# Test CI/CD mode explicitly
hatch run specfact --mode cicd hello

# Test CoPilot mode explicitly
hatch run specfact --mode copilot hello

# Test invalid mode (should fail)
hatch run specfact --mode invalid hello

# Test short form -m flag
hatch run specfact -m cicd hello
```

### Quick Test Script

Run the automated test script:

```bash
# Python-based test (recommended)
python3 test_mode_practical.py

# Or using hatch
hatch run python test_mode_practical.py
```

This script tests all detection scenarios automatically.

### 2. Test Environment Variable

```bash
# Set environment variable and test
export SPECFACT_MODE=copilot
specfact hello

# Set to CI/CD mode
export SPECFACT_MODE=cicd
specfact hello

# Unset to test default
unset SPECFACT_MODE
specfact hello  # Should default to CI/CD
```

### 3. Test Auto-Detection

#### Test CoPilot API Detection

```bash
# Simulate CoPilot API available
export COPILOT_API_URL=https://api.copilot.com
specfact hello  # Should detect CoPilot mode

# Or with token
export COPILOT_API_TOKEN=token123
specfact hello  # Should detect CoPilot mode

# Or with GitHub Copilot token
export GITHUB_COPILOT_TOKEN=token123
specfact hello  # Should detect CoPilot mode
```

#### Test IDE Detection

```bash
# Simulate VS Code environment
export VSCODE_PID=12345
export COPILOT_ENABLED=true
specfact hello  # Should detect CoPilot mode

# Simulate Cursor environment
export CURSOR_PID=12345
export CURSOR_COPILOT_ENABLED=true
specfact hello  # Should detect CoPilot mode

# Simulate VS Code via TERM_PROGRAM
export TERM_PROGRAM=vscode
export VSCODE_COPILOT_ENABLED=true
specfact hello  # Should detect CoPilot mode
```

### 4. Test Priority Order

```bash
# Test that explicit flag overrides environment
export SPECFACT_MODE=copilot
specfact --mode cicd hello  # Should use CI/CD mode (flag wins)

# Test that explicit flag overrides auto-detection
export COPILOT_API_URL=https://api.copilot.com
specfact --mode cicd hello  # Should use CI/CD mode (flag wins)
```

### 5. Test Default Behavior

```bash
# Clean environment - should default to CI/CD
unset SPECFACT_MODE
unset COPILOT_API_URL
unset COPILOT_API_TOKEN
unset GITHUB_COPILOT_TOKEN
unset VSCODE_PID
unset CURSOR_PID
specfact hello  # Should default to CI/CD mode
```

## Python Interactive Testing

You can also test the detection logic directly in Python using hatch:

```bash
# Test explicit mode
hatch run python -c "from specfact_cli.modes import OperationalMode, detect_mode; mode = detect_mode(explicit_mode=OperationalMode.CICD); print(f'Explicit CI/CD: {mode}')"

# Test environment variable
SPECFACT_MODE=copilot hatch run python -c "from specfact_cli.modes import OperationalMode, detect_mode; import os; mode = detect_mode(explicit_mode=None); print(f'Environment Copilot: {mode}')"

# Test default
hatch run python -c "from specfact_cli.modes import OperationalMode, detect_mode; import os; os.environ.clear(); mode = detect_mode(explicit_mode=None); print(f'Default: {mode}')"
```

Or use the practical test script:

```bash
hatch run python test_mode_practical.py
```

## Testing Command Routing (Phase 3.2+)

### Current State (Phase 3.2)

**Important**: In Phase 3.2, mode detection and routing infrastructure is complete, but **actual command execution is identical** for both modes. The only difference is the log message. Actual mode-specific behavior will be implemented in Phase 4.

### Test with Actual Commands

The `import from-code` command now uses mode-aware routing. You should see mode information in the output (but execution is the same for now):

```bash
# Test with CI/CD mode
hatch run specfact --mode cicd import from-code --repo . --confidence 0.5 --shadow-only

# Expected output:
# Mode: CI/CD (direct execution)
# Analyzing repository: .
# ...
```

```bash
# Test with CoPilot mode
hatch run specfact --mode copilot import from-code --repo . --confidence 0.5 --shadow-only

# Expected output:
# Mode: CoPilot (agent routing)
# Analyzing repository: .
# ...
```

### Test Router Directly

You can also test the routing logic directly in Python:

```bash
# Test router with CI/CD mode
hatch run python -c "
from specfact_cli.modes import OperationalMode, get_router
router = get_router()
result = router.route('import from-code', OperationalMode.CICD, {})
print(f'Mode: {result.mode}')
print(f'Execution mode: {result.execution_mode}')
"

# Test router with CoPilot mode
hatch run python -c "
from specfact_cli.modes import OperationalMode, get_router
router = get_router()
result = router.route('import from-code', OperationalMode.COPILOT, {})
print(f'Mode: {result.mode}')
print(f'Execution mode: {result.execution_mode}')
"
```

## Real-World Scenarios

### Scenario 1: CI/CD Pipeline

```bash
# In GitHub Actions or CI/CD
# No environment variables set
# Should auto-detect CI/CD mode
hatch run specfact import from-code --repo . --confidence 0.7

# Expected: Mode: CI/CD (direct execution)
```

### Scenario 2: Developer with CoPilot

```bash
# Developer running in VS Code/Cursor with CoPilot enabled
# IDE environment variables automatically set
# Should auto-detect CoPilot mode
hatch run specfact import from-code --repo . --confidence 0.7

# Expected: Mode: CoPilot (agent routing)
```

### Scenario 3: Force Mode Override

```bash
# Developer wants CI/CD mode even though CoPilot is available
hatch run specfact --mode cicd import from-code --repo . --confidence 0.7

# Expected: Mode: CI/CD (direct execution) - flag overrides auto-detection
```

## Verification Script

Here's a simple script to test all scenarios:

```bash
#!/bin/bash
# test-mode-detection.sh

echo "=== Testing Mode Detection ==="
echo

echo "1. Testing explicit CI/CD mode:"
specfact --mode cicd hello
echo

echo "2. Testing explicit CoPilot mode:"
specfact --mode copilot hello
echo

echo "3. Testing invalid mode (should fail):"
specfact --mode invalid hello 2>&1 || echo "✓ Failed as expected"
echo

echo "4. Testing SPECFACT_MODE environment variable:"
export SPECFACT_MODE=copilot
specfact hello
unset SPECFACT_MODE
echo

echo "5. Testing CoPilot API detection:"
export COPILOT_API_URL=https://api.copilot.com
specfact hello
unset COPILOT_API_URL
echo

echo "6. Testing default (no overrides):"
specfact hello
echo

echo "=== All Tests Complete ==="
```

## Debugging Mode Detection

To see what mode is being detected, you can add debug output:

```python
# In Python
from specfact_cli.modes import detect_mode, OperationalMode
import os

mode = detect_mode(explicit_mode=None)
print(f"Detected mode: {mode}")
print(f"Environment variables:")
print(f"  SPECFACT_MODE: {os.environ.get('SPECFACT_MODE', 'not set')}")
print(f"  COPILOT_API_URL: {os.environ.get('COPILOT_API_URL', 'not set')}")
print(f"  VSCODE_PID: {os.environ.get('VSCODE_PID', 'not set')}")
print(f"  CURSOR_PID: {os.environ.get('CURSOR_PID', 'not set')}")
```

## Expected Results

| Scenario | Expected Mode | Notes |
|----------|---------------|-------|
| `--mode cicd` | CICD | Explicit flag (highest priority) |
| `--mode copilot` | COPILOT | Explicit flag (highest priority) |
| `SPECFACT_MODE=copilot` | COPILOT | Environment variable |
| `COPILOT_API_URL` set | COPILOT | Auto-detection |
| `VSCODE_PID` + `COPILOT_ENABLED=true` | COPILOT | IDE detection |
| Clean environment | CICD | Default fallback |
| Invalid mode | Error | Validation rejects invalid values |
