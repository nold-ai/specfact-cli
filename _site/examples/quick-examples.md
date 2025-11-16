# Quick Examples

Quick code snippets for common SpecFact CLI tasks.

## Installation

```bash
# Zero-install (no setup required)
uvx --from specfact-cli specfact --help

# Install with pip
pip install specfact-cli

# Install in virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install specfact-cli

```

## Your First Command

```bash
# Starting a new project?
specfact plan init --interactive

# Have existing code?
specfact import from-code --repo . --name my-project

# Using GitHub Spec-Kit?
specfact import from-spec-kit --repo ./my-project --dry-run

```

## Import from Spec-Kit

```bash
# Preview migration
specfact import from-spec-kit --repo ./spec-kit-project --dry-run

# Execute migration
specfact import from-spec-kit --repo ./spec-kit-project --write

# With custom branch
specfact import from-spec-kit \
  --repo ./spec-kit-project \
  --write \
  --out-branch feat/specfact-migration

```

## Import from Code

```bash
# Basic import
specfact import from-code --repo . --name my-project

# With confidence threshold
specfact import from-code --repo . --confidence 0.7

# Shadow mode (observe only)
specfact import from-code --repo . --shadow-only

# CoPilot mode (enhanced prompts)
specfact --mode copilot import from-code --repo . --confidence 0.7

```

## Plan Management

```bash
# Initialize plan
specfact plan init --interactive

# Add feature
specfact plan add-feature \
  --key FEATURE-001 \
  --title "User Authentication" \
  --outcomes "Users can login securely"

# Add story
specfact plan add-story \
  --feature FEATURE-001 \
  --title "As a user, I can login with email and password" \
  --acceptance "Login form validates input"

```

## Plan Comparison

```bash
# Quick comparison (auto-detects plans)
specfact plan compare --repo .

# Explicit comparison
specfact plan compare \
  --manual .specfact/plans/main.bundle.yaml \
  --auto .specfact/reports/brownfield/auto-derived.*.yaml

# Code vs plan comparison
specfact plan compare --code-vs-plan --repo .

```

## Sync Operations

```bash
# One-time Spec-Kit sync
specfact sync spec-kit --repo . --bidirectional

# Watch mode (continuous sync)
specfact sync spec-kit --repo . --bidirectional --watch --interval 5

# Repository sync
specfact sync repository --repo . --target .specfact

# Repository watch mode
specfact sync repository --repo . --watch --interval 5

```

## Enforcement

```bash
# Shadow mode (observe only)
specfact enforce stage --preset minimal

# Balanced mode (block HIGH, warn MEDIUM)
specfact enforce stage --preset balanced

# Strict mode (block everything)
specfact enforce stage --preset strict

```

## Validation

```bash
# Quick validation
specfact repro

# Verbose validation
specfact repro --verbose

# With budget
specfact repro --verbose --budget 120

# Apply auto-fixes
specfact repro --fix --budget 120

```

## IDE Integration

```bash
# Initialize Cursor integration
specfact init --ide cursor

# Initialize VS Code integration
specfact init --ide vscode

# Force reinitialize
specfact init --ide cursor --force

```

## Operational Modes

```bash
# Auto-detect mode (default)
specfact import from-code --repo .

# Force CI/CD mode
specfact --mode cicd import from-code --repo .

# Force CoPilot mode
specfact --mode copilot import from-code --repo .

# Set via environment variable
export SPECFACT_MODE=copilot
specfact import from-code --repo .
```

## Common Workflows

### Daily Development

```bash
# Morning: Check status
specfact repro --verbose
specfact plan compare --repo .

# During development: Watch mode
specfact sync repository --repo . --watch --interval 5

# Before committing: Validate
specfact repro
specfact plan compare --repo .

```

### Migration from Spec-Kit

```bash
# Step 1: Preview
specfact import from-spec-kit --repo . --dry-run

# Step 2: Execute
specfact import from-spec-kit --repo . --write

# Step 3: Set up sync
specfact sync spec-kit --repo . --bidirectional --watch --interval 5

# Step 4: Enable enforcement
specfact enforce stage --preset minimal

```

### Brownfield Analysis

```bash
# Step 1: Analyze code
specfact import from-code --repo . --confidence 0.7

# Step 2: Review plan
cat .specfact/reports/brownfield/auto-derived.*.yaml

# Step 3: Compare with manual plan
specfact plan compare --repo .

# Step 4: Set up watch mode
specfact sync repository --repo . --watch --interval 5
```

## Advanced Examples

### Custom Output Path

```bash
specfact import from-code \
  --repo . \
  --name my-project \
  --out custom/path/my-plan.bundle.yaml

```

### Custom Report

```bash
specfact import from-code \
  --repo . \
  --report analysis-report.md

specfact plan compare \
  --repo . \
  --output comparison-report.md

```

### Feature Key Format

```bash
# Classname format (default for auto-derived)
specfact import from-code --repo . --key-format classname

# Sequential format (for manual plans)
specfact import from-code --repo . --key-format sequential

```

### Confidence Threshold

```bash
# Lower threshold (more features, lower confidence)
specfact import from-code --repo . --confidence 0.3

# Higher threshold (fewer features, higher confidence)
specfact import from-code --repo . --confidence 0.8
```

## Related Documentation

- [Getting Started](../getting-started/README.md) - Installation and first steps
- [First Steps](../getting-started/first-steps.md) - Step-by-step first commands
- [Use Cases](use-cases.md) - Detailed use case scenarios
- [Workflows](../guides/workflows.md) - Common daily workflows
- [Command Reference](../reference/commands.md) - Complete command reference

---

**Happy building!** 🚀
