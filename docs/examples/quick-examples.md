# Quick Examples

Quick code snippets for common SpecFact CLI tasks.

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow (VS Code, Cursor, GitHub Actions, pre-commit hooks). No platform to learn, no vendor lock-in.

## Installation

```bash
# Zero-install (no setup required) - CLI-only mode
uvx specfact-cli@latest --help

# Install with pip - Interactive AI Assistant mode
pip install specfact-cli

# Install in virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install specfact-cli

```

## Your First Command

```bash
# Starting a new project?
specfact plan init my-project --interactive

# Have existing code?
specfact import from-code my-project --repo .

# Using GitHub Spec-Kit?
specfact import from-bridge --adapter speckit --repo ./my-project --dry-run

```

## Import from Spec-Kit (via Bridge)

```bash
# Preview migration
specfact import from-bridge --adapter speckit --repo ./spec-kit-project --dry-run

# Execute migration
specfact import from-bridge --adapter speckit --repo ./spec-kit-project --write

```

## Import from Code

```bash
# Basic import (bundle name as positional argument)
specfact import from-code my-project --repo .

# With confidence threshold
specfact import from-code my-project --repo . --confidence 0.7

# Shadow mode (observe only)
specfact import from-code my-project --repo . --shadow-only

# CoPilot mode (enhanced prompts)
specfact --mode copilot import from-code my-project --repo . --confidence 0.7

```

## Plan Management

```bash
# Initialize plan (bundle name as positional argument)
specfact plan init my-project --interactive

# Add feature (bundle name via --bundle option)
specfact plan add-feature \
  --bundle my-project \
  --key FEATURE-001 \
  --title "User Authentication" \
  --outcomes "Users can login securely"

# Add story (bundle name via --bundle option)
specfact plan add-story \
  --bundle my-project \
  --feature FEATURE-001 \
  --title "As a user, I can login with email and password" \
  --acceptance "Login form validates input"

# Create hard SDD manifest (required for promotion)
specfact plan harden my-project

# Review plan (checks SDD automatically, bundle name as positional argument)
specfact plan review my-project --max-questions 5

# Promote plan (requires SDD for review+ stages)
specfact plan promote my-project --stage review

```

## Plan Comparison

```bash
# Quick comparison (auto-detects plans)
specfact plan compare --repo .

# Explicit comparison (bundle directory paths)
specfact plan compare \
  --manual .specfact/projects/manual-plan \
  --auto .specfact/projects/auto-derived

# Code vs plan comparison
specfact plan compare --code-vs-plan --repo .

```

## Sync Operations

```bash
# One-time Spec-Kit sync (via bridge adapter)
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional

# Watch mode (continuous sync)
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch --interval 5

# Repository sync
specfact sync repository --repo . --target .specfact

# Repository watch mode
specfact sync repository --repo . --watch --interval 5

```

## SDD (Spec-Driven Development) Workflow

```bash
# Create hard SDD manifest from plan
specfact plan harden

# Validate SDD manifest against plan
specfact enforce sdd

# Validate SDD with custom output format
specfact enforce sdd --output-format json --out validation-report.json

# Review plan (automatically checks SDD)
specfact plan review --max-questions 5

# Promote plan (requires SDD for review+ stages)
specfact plan promote --stage review

# Force promotion despite SDD validation failures
specfact plan promote --stage review --force
```

## Enforcement

```bash
# Shadow mode (observe only)
specfact enforce stage --preset minimal

# Balanced mode (block HIGH, warn MEDIUM)
specfact enforce stage --preset balanced

# Strict mode (block everything)
specfact enforce stage --preset strict

# Enforce SDD validation
specfact enforce sdd

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
specfact import from-code my-project --repo .

# Force CI/CD mode
specfact --mode cicd import from-code my-project --repo .

# Force CoPilot mode
specfact --mode copilot import from-code my-project --repo .

# Set via environment variable
export SPECFACT_MODE=copilot
specfact import from-code my-project --repo .
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

### Brownfield Modernization (Hard-SDD Workflow)

```bash
# Step 1: Extract specs from legacy code
specfact import from-code my-project --repo .

# Step 2: Create hard SDD manifest
specfact plan harden my-project

# Step 3: Validate SDD before starting work
specfact enforce sdd my-project

# Step 4: Review plan (checks SDD automatically)
specfact plan review my-project --max-questions 5

# Step 5: Promote plan (requires SDD for review+ stages)
specfact plan promote my-project --stage review

# Step 6: Add contracts to critical paths
# ... (add @icontract decorators to code)

# Step 7: Re-validate SDD after adding contracts
specfact enforce sdd my-project

# Step 8: Continue modernization with SDD safety net
```

### Migration from Spec-Kit

```bash
# Step 1: Preview
specfact import from-bridge --adapter speckit --repo . --dry-run

# Step 2: Execute
specfact import from-bridge --adapter speckit --repo . --write

# Step 3: Set up sync
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch --interval 5

# Step 4: Enable enforcement
specfact enforce stage --preset minimal

```

### Brownfield Analysis

```bash
# Step 1: Analyze code
specfact import from-code my-project --repo . --confidence 0.7

# Step 2: Review plan using CLI commands
specfact plan review my-project

# Step 3: Compare with manual plan
specfact plan compare --repo .

# Step 4: Set up watch mode
specfact sync repository --repo . --watch --interval 5
```

## Advanced Examples

### Bundle Name

```bash
# Bundle name is a positional argument (not --name option)
specfact import from-code my-project --repo .

```

### Custom Report

```bash
specfact import from-code \
  --repo . \
  --report analysis-report.md

specfact plan compare \
  --repo . \
  --out comparison-report.md

```

### Feature Key Format

```bash
# Classname format (default for auto-derived)
specfact import from-code my-project --repo . --key-format classname

# Sequential format (for manual plans)
specfact import from-code my-project --repo . --key-format sequential

```

### Confidence Threshold

```bash
# Lower threshold (more features, lower confidence)
specfact import from-code my-project --repo . --confidence 0.3

# Higher threshold (fewer features, higher confidence)
specfact import from-code my-project --repo . --confidence 0.8
```

## Integration Examples

- **[Integration Showcases](integration-showcases/)** ⭐ - Real bugs fixed via VS Code, Cursor, GitHub Actions integrations
- **[IDE Integration](../guides/ide-integration.md)** - Set up slash commands in your IDE

## Related Documentation

- [Getting Started](../getting-started/README.md) - Installation and first steps
- [First Steps](../getting-started/first-steps.md) - Step-by-step first commands
- [Use Cases](../guides/use-cases.md) - Detailed use case scenarios
- [Workflows](../guides/workflows.md) - Common daily workflows
- [Command Reference](../reference/commands.md) - Complete command reference

---

**Happy building!** 🚀
