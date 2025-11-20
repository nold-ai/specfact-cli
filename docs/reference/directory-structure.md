# SpecFact CLI Directory Structure

This document defines the canonical directory structure for SpecFact CLI artifacts.

> **Primary Use Case**: SpecFact CLI is designed for **brownfield code modernization** - reverse-engineering existing codebases into documented specs with runtime contract enforcement. The directory structure reflects this brownfield-first approach.

## Overview

All SpecFact artifacts are stored under `.specfact/` in the repository root. This ensures:

- **Consistency**: All artifacts in one predictable location
- **Multiple plans**: Support for multiple plan bundles in a single repository
- **Gitignore-friendly**: Easy to exclude reports from version control
- **Clear separation**: Plans (versioned) vs reports (ephemeral)

## Canonical Structure

```bash
.specfact/
├── config.yaml              # SpecFact configuration (optional)
├── plans/                   # Plan bundles (versioned in git)
│   ├── config.yaml          # Active plan configuration
│   ├── main.bundle.yaml     # Primary plan bundle (fallback)
│   ├── feature-auth.bundle.yaml    # Feature-specific plan
│   └── my-project-2025-10-31T14-30-00.bundle.yaml  # Brownfield-derived plan (timestamped with name)
├── protocols/               # FSM protocol definitions (versioned)
│   ├── workflow.protocol.yaml
│   └── deployment.protocol.yaml
├── reports/                 # Analysis reports (gitignored)
│   ├── brownfield/
│   │   └── analysis-2025-10-31T14-30-00.md  # Analysis reports only (not plan bundles)
│   ├── comparison/
│   │   ├── report-2025-10-31T14-30-00.md
│   │   └── report-2025-10-31T14-30-00.json
│   ├── enforcement/
│   │   └── gate-results-2025-10-31.json
│   └── sync/
│       ├── speckit-sync-2025-10-31.json
│       └── repository-sync-2025-10-31.json
├── gates/                   # Enforcement configuration and results
│   ├── config.yaml          # Enforcement settings
│   └── results/             # Historical gate results (gitignored)
│       ├── pr-123.json
│       └── pr-124.json
└── cache/                   # Tool caches (gitignored)
    ├── dependency-graph.json
    └── commit-history.json
```

## Directory Purposes

### `.specfact/plans/` (Versioned)

**Purpose**: Store plan bundles that define the contract for the project.

**Guidelines**:

- One primary `main.bundle.yaml` for the main project plan
- Additional plans for **brownfield analysis** ⭐ (primary), features, or experiments
- **Always committed to git** - these are the source of truth
- Use descriptive names: `legacy-<component>.bundle.yaml` (brownfield), `feature-<name>.bundle.yaml`

**Plan Bundle Structure:**

Plan bundles are YAML files with the following structure:

```yaml
version: "1.1"  # Schema version (current: 1.1)

metadata:
  stage: "draft"  # draft, review, approved, released
  summary:  # Summary metadata for fast access (added in v1.1)
    features_count: 5
    stories_count: 12
    themes_count: 2
    releases_count: 1
    content_hash: "abc123def456..."  # SHA256 hash for integrity
    computed_at: "2025-01-15T10:30:00"

idea:
  title: "Project Title"
  narrative: "Project description"
  # ... other idea fields

product:
  themes: ["Theme1", "Theme2"]
  releases: [...]

features:
  - key: "FEATURE-001"
    title: "Feature Title"
    stories: [...]
    # ... other feature fields
```

**Summary Metadata (v1.1+):**

Plan bundles version 1.1 and later include summary metadata in the `metadata.summary` section. This provides:

- **Fast access**: Read plan counts without parsing entire file (44% faster performance)
- **Integrity verification**: Content hash detects plan modifications
- **Performance optimization**: Only reads first 50KB for large files (>10MB)

**Upgrading Plan Bundles:**

Use `specfact plan upgrade` to migrate older plan bundles to the latest schema:

```bash
# Upgrade active plan
specfact plan upgrade

# Upgrade all plans
specfact plan upgrade --all

# Preview upgrades
specfact plan upgrade --dry-run
```

See [`plan upgrade`](../reference/commands.md#plan-upgrade) for details.

**Example**:

```bash
.specfact/plans/
├── main.bundle.yaml                    # Primary plan
├── legacy-api.bundle.yaml              # ⭐ Reverse-engineered from existing API (brownfield)
├── legacy-payment.bundle.yaml          # ⭐ Reverse-engineered from existing payment system (brownfield)
└── feature-authentication.bundle.yaml  # Auth feature plan
```

### `.specfact/protocols/` (Versioned)

**Purpose**: Store FSM (Finite State Machine) protocol definitions.

**Guidelines**:

- Define valid states and transitions
- **Always committed to git**
- Used for workflow validation

**Example**:

```bash
.specfact/protocols/
├── development-workflow.protocol.yaml
└── deployment-pipeline.protocol.yaml
```

### `.specfact/reports/` (Gitignored)

**Purpose**: Ephemeral analysis and comparison reports.

**Guidelines**:

- **Gitignored** - regenerated on demand
- Organized by report type (brownfield, comparison, enforcement)
- Include timestamps in filenames for historical tracking

**Example**:

```bash
.specfact/reports/
├── brownfield/
│   ├── analysis-2025-10-31T14-30-00.md
│   └── auto-derived-2025-10-31T14-30-00.bundle.yaml
├── comparison/
│   ├── report-2025-10-31T14-30-00.md
│   └── report-2025-10-31T14-30-00.json
└── sync/
    ├── speckit-sync-2025-10-31.json
    └── repository-sync-2025-10-31.json
```

### `.specfact/gates/` (Mixed)

**Purpose**: Enforcement configuration and gate execution results.

**Guidelines**:

- `config.yaml` is versioned (defines enforcement policy)
- `results/` is gitignored (execution logs)

**Example**:

```bash
.specfact/gates/
├── config.yaml              # Versioned: enforcement policy
└── results/                 # Gitignored: execution logs
    ├── pr-123.json
    └── commit-abc123.json
```

### `.specfact/cache/` (Gitignored)

**Purpose**: Tool caches for faster execution.

**Guidelines**:

- **Gitignored** - optimization only
- Safe to delete anytime
- Automatically regenerated

## Default Command Paths

### `specfact import from-code` ⭐ PRIMARY

**Primary use case**: Reverse-engineer existing codebases into plan bundles.

```bash
# Default paths (timestamped with custom name)
--out .specfact/plans/<name>-*.bundle.yaml  # Plan bundle (versioned in git)
--report .specfact/reports/brownfield/analysis-*.md  # Analysis report (gitignored)

# Can override with custom names
--out .specfact/plans/legacy-api.bundle.yaml  # Save as versioned plan
--name my-project  # Custom plan name (sanitized for filesystem)
```

**Example (brownfield modernization)**:

```bash
# Analyze legacy codebase
specfact import from-code --repo . --name legacy-api --confidence 0.7

# Creates:
# - .specfact/plans/legacy-api-2025-10-31T14-30-00.bundle.yaml (versioned)
# - .specfact/reports/brownfield/analysis-2025-10-31T14-30-00.md (gitignored)
```

### `specfact plan init` (Alternative)

**Alternative use case**: Create new plans for greenfield projects.

```bash
# Creates
.specfact/plans/main.bundle.yaml
.specfact/config.yaml (if --interactive)
```

### `specfact plan compare`

```bash
# Default paths (smart defaults)
--manual .specfact/plans/active-plan  # Uses active plan from config.yaml (or main.bundle.yaml fallback)
--auto .specfact/plans/*.bundle.yaml  # Latest auto-derived in plans directory
--out .specfact/reports/comparison/report-*.md  # Timestamped
```

### `specfact sync spec-kit`

```bash
# Sync changes
specfact sync spec-kit --repo . --bidirectional

# Watch mode
specfact sync spec-kit --repo . --bidirectional --watch --interval 5

# Sync files are tracked in .specfact/sync/
```

### `specfact sync repository`

```bash
# Sync code changes
specfact sync repository --repo . --target .specfact

# Watch mode
specfact sync repository --repo . --watch --interval 5

# Sync reports in .specfact/reports/sync/
```

### `specfact enforce stage`

```bash
# Reads/writes
.specfact/gates/config.yaml
```

### `specfact init`

Initializes IDE integration by copying prompt templates to IDE-specific locations:

```bash
# Auto-detect IDE
specfact init

# Specify IDE explicitly
specfact init --ide cursor
specfact init --ide vscode
specfact init --ide copilot
```

**Creates IDE-specific directories:**

- **Cursor**: `.cursor/commands/` (markdown files)
- **VS Code / Copilot**: `.github/prompts/` (`.prompt.md` files) + `.vscode/settings.json`
- **Claude Code**: `.claude/commands/` (markdown files)
- **Gemini**: `.gemini/commands/` (TOML files)
- **Qwen**: `.qwen/commands/` (TOML files)
- **Other IDEs**: See [IDE Integration Guide](../guides/ide-integration.md)

**See [IDE Integration Guide](../guides/ide-integration.md)** for complete setup instructions.

## Configuration File

`.specfact/config.yaml` (optional):

```yaml
version: "1.0"

# Default plan to use
default_plan: plans/main.bundle.yaml

# Analysis settings
analysis:
  confidence_threshold: 0.7
  exclude_patterns:
    - "**/__pycache__/**"
    - "**/node_modules/**"
    - "**/venv/**"

# Enforcement settings
enforcement:
  preset: balanced  # strict, balanced, minimal, shadow
  budget_seconds: 120
  fail_fast: false

# Repro settings
repro:
  parallel: true
  timeout: 300
```

## IDE Integration Directories

When you run `specfact init`, prompt templates are copied to IDE-specific locations for slash command integration.

### IDE-Specific Locations

| IDE | Directory | Format | Settings File |
|-----|-----------|--------|---------------|
| **Cursor** | `.cursor/commands/` | Markdown | None |
| **VS Code / Copilot** | `.github/prompts/` | `.prompt.md` | `.vscode/settings.json` |
| **Claude Code** | `.claude/commands/` | Markdown | None |
| **Gemini** | `.gemini/commands/` | TOML | None |
| **Qwen** | `.qwen/commands/` | TOML | None |
| **opencode** | `.opencode/command/` | Markdown | None |
| **Windsurf** | `.windsurf/workflows/` | Markdown | None |
| **Kilo Code** | `.kilocode/workflows/` | Markdown | None |
| **Auggie** | `.augment/commands/` | Markdown | None |
| **Roo Code** | `.roo/commands/` | Markdown | None |
| **CodeBuddy** | `.codebuddy/commands/` | Markdown | None |
| **Amp** | `.agents/commands/` | Markdown | None |
| **Amazon Q** | `.amazonq/prompts/` | Markdown | None |

### Example Structure (Cursor)

```bash
.cursor/
└── commands/
    ├── specfact-import-from-code.md
    ├── specfact-plan-init.md
    ├── specfact-plan-promote.md
    ├── specfact-plan-compare.md
    └── specfact-sync.md
```

### Example Structure (VS Code / Copilot)

```bash
.github/
└── prompts/
    ├── specfact-import-from-code.prompt.md
    ├── specfact-plan-init.prompt.md
    ├── specfact-plan-promote.prompt.md
    ├── specfact-plan-compare.prompt.md
    └── specfact-sync.prompt.md
.vscode/
└── settings.json  # Updated with promptFilesRecommendations
```

**Guidelines:**

- **Versioned** - IDE directories are typically committed to git (team-shared configuration)
- **Templates** - Prompt templates are read-only for the IDE, not modified by users
- **Settings** - VS Code `settings.json` is merged (not overwritten) to preserve existing settings
- **Auto-discovery** - IDEs automatically discover and register templates as slash commands

**See [IDE Integration Guide](../guides/ide-integration.md)** for detailed setup and usage.

---

## SpecFact CLI Package Structure

The SpecFact CLI package includes prompt templates that are copied to IDE locations:

```bash
specfact-cli/
└── resources/
    └── prompts/              # Prompt templates (in package)
        ├── specfact-import-from-code.md
        ├── specfact-plan-init.md
        ├── specfact-plan-promote.md
        ├── specfact-plan-compare.md
        └── specfact-sync.md
```

**These templates are:**

- Packaged with SpecFact CLI
- Copied to IDE locations by `specfact init`
- Not modified by users (read-only templates)

---

## `.gitignore` Recommendations

Add to `.gitignore`:

```gitignore
# SpecFact ephemeral artifacts
.specfact/reports/
.specfact/gates/results/
.specfact/cache/

# Keep these versioned
!.specfact/plans/
!.specfact/protocols/
!.specfact/config.yaml
!.specfact/gates/config.yaml

# IDE integration directories (optional - typically versioned)
# Uncomment if you don't want to commit IDE integration files
# .cursor/commands/
# .github/prompts/
# .vscode/settings.json
# .claude/commands/
# .gemini/commands/
# .qwen/commands/
```

**Note**: IDE integration directories are typically **versioned** (committed to git) so team members share the same slash commands. However, you can gitignore them if preferred.

## Migration from Old Structure

If you have existing artifacts in other locations:

```bash
# Old structure
contracts/plans/plan.bundle.yaml
reports/analysis.md

# New structure
.specfact/plans/main.bundle.yaml
.specfact/reports/brownfield/analysis.md

# Migration
mkdir -p .specfact/plans .specfact/reports/brownfield
mv contracts/plans/plan.bundle.yaml .specfact/plans/main.bundle.yaml
mv reports/analysis.md .specfact/reports/brownfield/
```

## Multiple Plans in One Repository

SpecFact supports multiple plan bundles for:

- **Brownfield modernization** ⭐ **PRIMARY**: Separate plans for legacy components vs modernized code
- **Monorepos**: One plan per service
- **Feature branches**: Feature-specific plans

**Example (Brownfield Modernization)**:

```bash
.specfact/plans/
├── main.bundle.yaml                      # Overall project plan
├── legacy-api.bundle.yaml                # ⭐ Reverse-engineered from existing API (brownfield)
├── legacy-payment.bundle.yaml            # ⭐ Reverse-engineered from existing payment system (brownfield)
├── modernized-api.bundle.yaml            # New API plan (after modernization)
└── feature-new-auth.bundle.yaml          # Experimental feature plan
```

**Usage (Brownfield Workflow)**:

```bash
# Step 1: Reverse-engineer legacy codebase
specfact import from-code \
  --repo src/legacy-api \
  --name legacy-api \
  --out .specfact/plans/legacy-api.bundle.yaml

# Step 2: Compare legacy vs modernized
specfact plan compare \
  --manual .specfact/plans/legacy-api.bundle.yaml \
  --auto .specfact/plans/modernized-api.bundle.yaml

# Step 3: Analyze specific legacy component
specfact import from-code \
  --repo src/legacy-payment \
  --name legacy-payment \
  --out .specfact/plans/legacy-payment.bundle.yaml
```

## Summary

### SpecFact Artifacts

- **`.specfact/`** - All SpecFact artifacts live here
- **`plans/` and `protocols/`** - Versioned (git)
- **`reports/`, `gates/results/`, `cache/`** - Gitignored (ephemeral)
- **Use descriptive plan names** - Supports multiple plans per repo
- **Default paths always start with `.specfact/`** - Consistent and predictable
- **Timestamped reports** - Auto-generated reports include timestamps for tracking
- **Sync support** - Bidirectional sync with Spec-Kit and repositories

### IDE Integration

- **IDE directories** - Created by `specfact init` (e.g., `.cursor/commands/`, `.github/prompts/`)
- **Prompt templates** - Copied from `resources/prompts/` in SpecFact CLI package
- **Typically versioned** - IDE directories are usually committed to git for team sharing
- **Auto-discovery** - IDEs automatically discover and register templates as slash commands
- **Settings files** - VS Code `settings.json` is merged (not overwritten)

### Quick Reference

| Type | Location | Git Status | Purpose |
|------|----------|------------|---------|
| **Plans** | `.specfact/plans/` | Versioned | Contract definitions |
| **Protocols** | `.specfact/protocols/` | Versioned | FSM definitions |
| **Reports** | `.specfact/reports/` | Gitignored | Analysis reports |
| **Cache** | `.specfact/cache/` | Gitignored | Tool caches |
| **IDE Templates** | `.cursor/commands/`, `.github/prompts/`, etc. | Versioned (recommended) | Slash command templates |
