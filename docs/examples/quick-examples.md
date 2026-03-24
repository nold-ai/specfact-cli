---
layout: default
title: Quick Examples
permalink: /examples/quick-examples/
redirect_from:
  - /quick-examples/
---

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
specfact project snapshot --bundle my-project

# Have existing code?
specfact code import my-project --repo .

# Using GitHub Spec-Kit?
specfact code import from-bridge --adapter speckit --repo ./my-project --dry-run

```

## Import from Spec-Kit (via Bridge)

```bash
# Preview migration
specfact code import from-bridge --adapter speckit --repo ./spec-kit-project --dry-run

# Execute migration
specfact code import from-bridge --adapter speckit --repo ./spec-kit-project --write

```

## Import from Code

```bash
# Basic import (bundle name as positional argument)
specfact code import my-project --repo .

# With confidence threshold
specfact code import my-project --repo . --confidence 0.7

# Shadow mode (observe only)
specfact code import my-project --repo . --shadow-only

# CoPilot mode (enhanced prompts)
specfact --mode copilot import from-code my-project --repo . --confidence 0.7

# Re-validate existing features (force re-analysis)
specfact code import my-project --repo . --revalidate-features

# Resume interrupted import (features saved early as checkpoint)
# If import is cancelled, just run the same command again
specfact code import my-project --repo .

# Partial analysis (analyze specific subdirectory only)
specfact code import my-project --repo . --entry-point src/core

# Large codebase with progress reporting
# Progress bars show: feature analysis, source linking, contract extraction
specfact code import large-project --repo . --confidence 0.5

```

## Plan Management

```bash
# Initialize plan (create a snapshot for a new bundle)
specfact project snapshot --bundle my-project

# Enforce SDD (validates plan and coverage thresholds)
specfact govern enforce sdd my-project

# Review plan (check health and SDD compliance)
specfact project health-check

# Promote plan to review stage
specfact project devops-flow --stage review --bundle my-project

```

## Plan Comparison

```bash
# Regenerate and compare plans
specfact project regenerate

```

## Sync Operations

```bash
# One-time Spec-Kit sync (via bridge adapter)
specfact project sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional

# Watch mode (continuous sync)
specfact project sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch --interval 5

# Repository sync
specfact project sync repository --repo . --target .specfact

# Repository watch mode
specfact project sync repository --repo . --watch --interval 5

```

## SDD (Spec-Driven Development) Workflow

```bash
# Validate SDD manifest against plan
specfact govern enforce sdd

# Validate SDD with custom output format
specfact govern enforce sdd --output-format json --out validation-report.json

# Review plan health (checks SDD automatically)
specfact project health-check

# Promote plan to review stage (requires SDD)
specfact project devops-flow --stage review --bundle <bundle>
```

## Enforcement

```bash
# Shadow mode (observe only)
specfact govern enforce stage --preset minimal

# Balanced mode (block HIGH, warn MEDIUM)
specfact govern enforce stage --preset balanced

# Strict mode (block everything)
specfact govern enforce stage --preset strict

# Enforce SDD validation
specfact govern enforce sdd

```

## Validation

```bash
# First-time setup: Configure CrossHair for contract exploration
specfact code repro setup

# Quick validation
specfact code repro

# Verbose validation
specfact code repro --verbose

# With budget
specfact code repro --verbose --budget 120

# Apply auto-fixes
specfact code repro --fix --budget 120

```

## IDE Integration

```bash
# Initialize Cursor integration
specfact init ide --ide cursor

# Initialize VS Code integration
specfact init ide --ide vscode

# Force reinitialize
specfact init ide --ide cursor --force

```

## Operational Modes

```bash
# Auto-detect mode (default)
specfact code import my-project --repo .

# Force CI/CD mode
specfact --mode cicd import from-code my-project --repo .

# Force CoPilot mode
specfact --mode copilot import from-code my-project --repo .

# Set via environment variable
export SPECFACT_MODE=copilot
specfact code import my-project --repo .
```

## Common Workflows

### Daily Development

```bash
# Morning: Check status
specfact code repro --verbose
specfact project regenerate

# During development: Watch mode
specfact project sync repository --repo . --watch --interval 5

# Before committing: Validate
specfact code repro
specfact project regenerate

```

### Brownfield Modernization (Hard-SDD Workflow)

```bash
# Step 1: Extract specs from legacy code
specfact code import my-project --repo .

# Step 2: Validate SDD and coverage thresholds
specfact govern enforce sdd my-project

# Step 3: Review plan health (checks SDD automatically)
specfact project health-check

# Step 4: Promote plan to review stage (requires SDD)
specfact project devops-flow --stage review --bundle my-project

# Step 5: Add contracts to critical paths
# ... (add @icontract decorators to code)

# Step 6: Re-validate SDD after adding contracts
specfact govern enforce sdd my-project

# Step 7: Continue modernization with SDD safety net
```

### Migration from Spec-Kit

```bash
# Step 1: Preview
specfact code import from-bridge --adapter speckit --repo . --dry-run

# Step 2: Execute
specfact code import from-bridge --adapter speckit --repo . --write

# Step 3: Set up sync
specfact project sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch --interval 5

# Step 4: Enable enforcement
specfact govern enforce stage --preset minimal

```

### Brownfield Analysis

```bash
# Step 1: Analyze code
specfact code import my-project --repo . --confidence 0.7

# Step 2: Review plan health
specfact project health-check

# Step 3: Regenerate and compare plans
specfact project regenerate

# Step 4: Set up watch mode
specfact project sync repository --repo . --watch --interval 5
```

## Advanced Examples

### Bundle Name

```bash
# Bundle name is a positional argument (not --name option)
specfact code import my-project --repo .

```

### Custom Report

```bash
specfact code import \
  --repo . \
  --report analysis-report.md

specfact project regenerate \
  --out comparison-report.md

```

### Feature Key Format

```bash
# Classname format (default for auto-derived)
specfact code import my-project --repo . --key-format classname

# Sequential format (for manual plans)
specfact code import my-project --repo . --key-format sequential

```

### Confidence Threshold

```bash
# Lower threshold (more features, lower confidence)
specfact code import my-project --repo . --confidence 0.3

# Higher threshold (fewer features, higher confidence)
specfact code import my-project --repo . --confidence 0.8
```

## Integration Examples

- **[Integration Showcases](integration-showcases/)** ⭐ - Real bugs fixed via VS Code, Cursor, GitHub Actions integrations
- **[IDE Integration](../guides/ide-integration.md)** - Set up slash commands in your IDE

## Related Documentation

- [Getting Started](../getting-started/README.md) - Installation and first steps
- [First Steps](../getting-started/quickstart.md) - Step-by-step first commands
- [Use Cases](../guides/use-cases.md) - Detailed use case scenarios
- Workflows - Common daily workflows
- [Command Reference](../reference/commands.md) - Complete command reference

---

**Happy building!** 🚀
