# Integration Showcases - Quick Reference

> **Quick command reference** for testing all 5 integration examples

---

## Setup (One-Time)

### Step 1: Verify Python Version

```bash
# Check Python version (requires 3.11+)
python3 --version
# Should show Python 3.11.x or higher
```

### Step 2: Install SpecFact

```bash
# Install via pip (required for interactive AI assistant)
pip install specfact-cli

# Verify installation
specfact --version
```

### Step 3: Create Test Cases

```bash
# Run setup script
./docs/examples/integration-showcases/setup-integration-tests.sh

# Or manually
mkdir -p /tmp/specfact-integration-tests
cd /tmp/specfact-integration-tests
```

### Step 4: Initialize IDE Integration (For Interactive Mode)

```bash
# Navigate to test directory
cd /tmp/specfact-integration-tests/example1_vscode

# Initialize SpecFact for your IDE (one-time per project)
specfact init

# Or specify IDE explicitly:
# specfact init --ide cursor
# specfact init --ide vscode
```

**⚠️ Important**: `specfact init` copies templates to the directory where you run it (e.g., `/tmp/specfact-integration-tests/example1_vscode/.cursor/commands/`). For slash commands to work correctly:

- **Open the demo repo in your IDE** as the workspace root (e.g., `/tmp/specfact-integration-tests/example1_vscode`)
- Interactive mode automatically uses your IDE workspace - no `--repo .` parameter needed
- **OR** if you need to analyze a different repository: `/specfact.01-import legacy-api --repo /path/to/other/repo`

---

## Example 1: VS Code - Async Bug

**⚠️ Prerequisite**: Open `/tmp/specfact-integration-tests/example1_vscode` as your IDE workspace.

```bash
cd /tmp/specfact-integration-tests/example1_vscode

# Step 1: Import code to create plan
# Recommended: Use interactive AI assistant (slash command in IDE)
# /specfact.01-import legacy-api --repo .
# (Interactive mode automatically uses IDE workspace - --repo . optional)
# The AI will prompt for a plan name - suggest: "Payment Processing"

# Alternative: CLI-only mode (bundle name as positional argument)
specfact --no-banner import from-code payment-processing --repo . --output-format yaml

# Step 2: Run enforcement
specfact --no-banner enforce stage --preset balanced

# Expected: Contract violation about blocking I/O
```

**Capture**: Full output, exit code (`echo $?`)

---

## Example 2: Cursor - Regression Prevention

```bash
cd /tmp/specfact-integration-tests/example2_cursor

# Step 1: Import code (bundle name as positional argument)
specfact --no-banner import from-code data-pipeline --repo . --output-format yaml

# Step 2: Test original (should pass)
specfact --no-banner enforce stage --preset balanced

# Step 3: Create broken version (remove None check)
# Edit src/pipeline.py to remove None check, then:
specfact --no-banner plan compare src/pipeline.py src/pipeline_broken.py --fail-on HIGH

# Expected: Contract violation for missing None check
```

**Capture**: Output from both commands

---

## Example 3: GitHub Actions - Type Error

```bash
cd /tmp/specfact-integration-tests/example3_github_actions

# Step 1: Import code (bundle name as positional argument)
specfact --no-banner import from-code user-api --repo . --output-format yaml

# Step 2: Run enforcement
specfact --no-banner enforce stage --preset balanced

# Expected: Type mismatch violation (int vs dict)
```

**Capture**: Full output, exit code

---

## Example 4: Pre-commit - Breaking Change

```bash
cd /tmp/specfact-integration-tests/example4_precommit

# Step 1: Initial commit (bundle name as positional argument)
specfact --no-banner import from-code order-processor --repo . --output-format yaml
git add .
git commit -m "Initial code"

# Step 2: Modify function (add user_id parameter)
# Edit src/legacy.py to add user_id parameter, then:
git add src/legacy.py
git commit -m "Breaking change test"

# Expected: Pre-commit hook blocks commit, shows breaking change
```

**Capture**: Pre-commit hook output, git commit result

---

## Example 5: Agentic - CrossHair Edge Case

```bash
cd /tmp/specfact-integration-tests/example5_agentic

# Option 1: CrossHair exploration (if available)
specfact --no-banner contract-test-exploration src/validator.py

# Option 2: Contract enforcement (fallback)
specfact --no-banner enforce stage --preset balanced

# Expected: Division by zero edge case detected
```

**Capture**: Output from exploration or enforcement

---

## Output Template

For each example, provide:

```markdown
# Example X: [Name]

## Command Executed

```bash
[exact command]
```

## Full Output

```bash
[complete stdout and stderr]
```

## Exit Code

```bash
[exit code from echo $?]
```

## Files Created

- [list of files]

## Issues Found

- [any problems or unexpected behavior]

## Expected vs Actual

- [comparison]

```text
[comparison details]
```

---

## Quick Test All

```bash
# Run all examples in sequence (bundle name as positional argument)
for dir in example1_vscode example2_cursor example3_github_actions example4_precommit example5_agentic; do
  echo "Testing $dir..."
  cd /tmp/specfact-integration-tests/$dir
  bundle_name=$(echo "$dir" | sed 's/example[0-9]_//')
  specfact --no-banner import from-code "$bundle_name" --repo . --output-format yaml 2>&1
  specfact --no-banner enforce stage --preset balanced 2>&1
  echo "---"
done
```

---

**Ready?** Start with Example 1 and work through each one!
