# SpecFact CLI Directory Structure

This document defines the canonical directory structure for SpecFact CLI artifacts.

> **Primary Use Case**: SpecFact CLI is designed for **brownfield code modernization** - reverse-engineering existing codebases into documented specs with runtime contract enforcement. The directory structure reflects this brownfield-first approach.

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow. Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE. No platform to learn, no vendor lock-in.

## Overview

All SpecFact artifacts are stored under `.specfact/` in the repository root. This ensures:

- **Consistency**: All artifacts in one predictable location
- **Multiple plans**: Support for multiple plan bundles in a single repository
- **Gitignore-friendly**: Easy to exclude reports from version control
- **Clear separation**: Plans (versioned) vs reports (ephemeral)
- **CLI-first**: All artifacts are local, no cloud storage required

## Canonical Structure

```bash
.specfact/
├── config.yaml              # SpecFact configuration (optional)
├── config/                  # Global configuration (optional)
│   ├── bridge.yaml          # Bridge configuration for external tools
│   └── ...
├── cache/                   # Shared cache (gitignored, global for performance)
│   ├── dependency-graph.json
│   └── commit-history.json
├── projects/                # Modular project bundles (versioned in git)
│   ├── <bundle-name>/       # Project bundle directory
│   │   ├── bundle.manifest.yaml  # Bundle metadata, versioning, and checksums
│   │   ├── idea.yaml             # Product vision (optional)
│   │   ├── business.yaml         # Business context (optional)
│   │   ├── product.yaml          # Releases, themes (required)
│   │   ├── clarifications.yaml   # Clarification sessions (optional)
│   │   ├── sdd.yaml              # SDD manifest (bundle-specific, Phase 8.5)
│   │   ├── tasks.yaml            # Task breakdown (bundle-specific, Phase 8.5)
│   │   ├── features/             # Individual feature files
│   │   │   ├── FEATURE-001.yaml
│   │   │   ├── FEATURE-002.yaml
│   │   │   └── ...
│   │   ├── contracts/            # OpenAPI contracts (bundle-specific)
│   │   │   └── ...
│   │   ├── protocols/            # FSM protocols (bundle-specific)
│   │   │   └── ...
│   │   ├── reports/              # Bundle-specific reports (gitignored, Phase 8.5)
│   │   │   ├── brownfield/
│   │   │   │   └── analysis-2025-10-31T14-30-00.md
│   │   │   ├── comparison/
│   │   │   │   └── report-2025-10-31T14-30-00.md
│   │   │   ├── enrichment/
│   │   │   │   └── <bundle-name>-2025-10-31T14-30-00.enrichment.md
│   │   │   └── enforcement/
│   │   │       └── report-2025-10-31T14-30-00.yaml
│   │   ├── logs/                 # Bundle-specific logs (gitignored, Phase 8.5)
│   │   │   └── 2025-10-31T14-30-00.log
│   │   └── prompts/              # AI IDE contract enhancement prompts (optional)
│   │       └── enhance-<filename>-<contracts>.md
│   ├── legacy-api/         # Example: Brownfield-derived bundle
│   │   ├── bundle.manifest.yaml
│   │   ├── product.yaml
│   │   ├── sdd.yaml
│   │   ├── tasks.yaml
│   │   ├── features/
│   │   ├── reports/
│   │   └── logs/
│   └── my-project/          # Example: Main project bundle
│       ├── bundle.manifest.yaml
│       ├── idea.yaml
│       ├── business.yaml
│       ├── product.yaml
│       ├── sdd.yaml
│       ├── tasks.yaml
│       ├── features/
│       ├── reports/
│       └── logs/
└── gates/                   # Enforcement configuration (global)
    └── config.yaml          # Enforcement settings (versioned)
```

## Directory Purposes

### `.specfact/projects/` (Versioned)

**Purpose**: Store modular project bundles that define the contract for the project.

**Guidelines**:

- Each project bundle is stored in its own directory: `.specfact/projects/<bundle-name>/`
- Each bundle directory contains multiple aspect files:
  - `bundle.manifest.yaml` - Bundle metadata, versioning, checksums, and feature index (required)
  - `product.yaml` - Product definition with themes and releases (required)
  - `idea.yaml` - Product vision and intent (optional)
  - `business.yaml` - Business context and market segments (optional)
  - `clarifications.yaml` - Clarification sessions and Q&A (optional)
  - `sdd.yaml` - SDD manifest (bundle-specific, Phase 8.5, versioned)
  - `tasks.yaml` - Task breakdown (bundle-specific, Phase 8.5, versioned)
  - `features/` - Directory containing individual feature files:
    - `FEATURE-001.yaml` - Individual feature with stories
    - `FEATURE-002.yaml` - Individual feature with stories
    - Each feature file is self-contained with its stories, acceptance criteria, etc.
  - `contracts/` - OpenAPI contract files (bundle-specific, versioned)
  - `protocols/` - FSM protocol definitions (bundle-specific, versioned)
  - `reports/` - Bundle-specific analysis reports (gitignored, Phase 8.5)
  - `logs/` - Bundle-specific execution logs (gitignored, Phase 8.5)
- **Always committed to git** - these are the source of truth (except reports/ and logs/)
- **Phase 8.5**: All bundle-specific artifacts are stored within bundle folders for better isolation
- Use descriptive bundle names: `legacy-api`, `my-project`, `feature-auth`
- Supports multiple bundles per repository for brownfield modernization, monorepos, or feature branches
- Aspect files are YAML format (JSON support may be added in future)

**Plan Bundle Structure:**

Plan bundles are YAML (or JSON) files with the following structure:

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
.specfact/projects/
├── my-project/                    # Primary project bundle
│   ├── bundle.manifest.yaml       # Metadata, checksums, feature index
│   ├── idea.yaml                  # Product vision
│   ├── business.yaml              # Business context
│   ├── product.yaml               # Themes and releases
│   ├── features/                  # Individual feature files
│   │   ├── FEATURE-001.yaml
│   │   ├── FEATURE-002.yaml
│   │   └── FEATURE-003.yaml
│   └── prompts/                   # AI IDE contract enhancement prompts (optional)
│       └── enhance-<filename>-<contracts>.md
├── legacy-api/                    # ⭐ Reverse-engineered from existing API (brownfield)
│   ├── bundle.manifest.yaml
│   ├── product.yaml
│   ├── features/
│   │   ├── FEATURE-AUTH.yaml
│   │   └── FEATURE-PAYMENT.yaml
│   └── prompts/                   # Bundle-specific prompts (avoids conflicts)
│       └── enhance-<filename>-<contracts>.md
├── legacy-payment/                 # ⭐ Reverse-engineered from existing payment system (brownfield)
│   ├── bundle.manifest.yaml
│   ├── product.yaml
│   └── features/
│       └── FEATURE-PAYMENT.yaml
└── feature-auth/                   # Auth feature bundle
    ├── bundle.manifest.yaml
    ├── product.yaml
    └── features/
        └── FEATURE-AUTH.yaml
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

### Bundle-Specific Artifacts (Phase 8.5)

**Phase 8.5 Update**: All bundle-specific artifacts are now stored within `.specfact/projects/<bundle-name>/` folders for better isolation and organization.

**Bundle-Specific Artifacts**:

- **Reports**: `.specfact/projects/<bundle-name>/reports/` (gitignored)
  - `brownfield/` - Brownfield analysis reports
  - `comparison/` - Plan comparison reports
  - `enrichment/` - LLM enrichment reports
  - `enforcement/` - SDD enforcement validation reports
- **SDD Manifests**: `.specfact/projects/<bundle-name>/sdd.yaml` (versioned)
- **Tasks**: `.specfact/projects/<bundle-name>/tasks.yaml` (versioned)
- **Logs**: `.specfact/projects/<bundle-name>/logs/` (gitignored)

**Migration**: Use `specfact migrate artifacts` to move existing artifacts from global locations to bundle-specific folders.

**Example**:

```bash
.specfact/projects/legacy-api/
├── bundle.manifest.yaml
├── product.yaml
├── sdd.yaml                    # Bundle-specific SDD manifest
├── tasks.yaml                  # Bundle-specific task breakdown
├── reports/                    # Bundle-specific reports (gitignored)
│   ├── brownfield/
│   │   └── analysis-2025-10-31T14-30-00.md
│   ├── comparison/
│   │   └── report-2025-10-31T14-30-00.md
│   ├── enrichment/
│   │   └── legacy-api-2025-10-31T14-30-00.enrichment.md
│   └── enforcement/
│       └── report-2025-10-31T14-30-00.yaml
└── logs/                       # Bundle-specific logs (gitignored)
    └── 2025-10-31T14-30-00.log
```

### Legacy Global Locations (Removed)

**Note**: The following global locations have been removed (Phase 8.5):

- ❌ `.specfact/plans/` - Removed (active bundle config migrated to `.specfact/config.yaml`)
- ❌ `.specfact/gates/results/` - Removed (enforcement reports are bundle-specific)
- ❌ `.specfact/reports/` - Removed (reports are bundle-specific)
- ❌ `.specfact/sdd/` - Removed (SDD manifests are bundle-specific)
- ❌ `.specfact/tasks/` - Removed (task files are bundle-specific)

**Migration**: Use `specfact migrate cleanup-legacy` to remove empty legacy directories, and `specfact migrate artifacts` to migrate existing artifacts to bundle-specific locations.

### `.specfact/gates/` (Versioned)

**Purpose**: Global enforcement configuration.

**Guidelines**:

- `config.yaml` is versioned (defines enforcement policy)
- Enforcement reports are bundle-specific (stored in `.specfact/projects/<bundle-name>/reports/enforcement/`)

**Example**:

```bash
.specfact/gates/
└── config.yaml              # Versioned: enforcement policy
```

**Note**: Enforcement execution reports are stored in bundle-specific locations (Phase 8.5):

- `.specfact/projects/<bundle-name>/reports/enforcement/report-<timestamp>.yaml`

### `.specfact/cache/` (Gitignored)

**Purpose**: Tool caches for faster execution.

**Guidelines**:

- **Gitignored** - optimization only
- Safe to delete anytime
- Automatically regenerated

## Default Command Paths

### `specfact import from-code` ⭐ PRIMARY

**Primary use case**: Reverse-engineer existing codebases into project bundles.

```bash
# Command syntax
specfact import from-code <bundle-name> --repo . [OPTIONS]

# Creates modular bundle at:
.specfact/projects/<bundle-name>/
├── bundle.manifest.yaml  # Bundle metadata, versioning, checksums, feature index
├── product.yaml          # Product definition (required)
├── idea.yaml            # Product vision (if provided)
├── business.yaml        # Business context (if provided)
└── features/            # Individual feature files
    ├── FEATURE-001.yaml
    ├── FEATURE-002.yaml
    └── ...

# Analysis report (bundle-specific, gitignored, Phase 8.5)
.specfact/projects/<bundle-name>/reports/brownfield/analysis-<timestamp>.md
```

**Example (brownfield modernization)**:

```bash
# Analyze legacy codebase
specfact import from-code legacy-api --repo . --confidence 0.7

# Creates:
# - .specfact/projects/legacy-api/bundle.manifest.yaml (versioned)
# - .specfact/projects/legacy-api/product.yaml (versioned)
# - .specfact/projects/legacy-api/features/FEATURE-*.yaml (versioned, one per feature)
# - .specfact/reports/brownfield/analysis-2025-10-31T14-30-00.md (gitignored)
```

### `specfact plan init` (Alternative)

**Alternative use case**: Create new project bundles for greenfield projects.

```bash
# Command syntax
specfact plan init <bundle-name> [OPTIONS]

# Creates modular bundle at:
.specfact/projects/<bundle-name>/
├── bundle.manifest.yaml  # Bundle metadata and versioning
├── product.yaml         # Product definition (required)
├── idea.yaml           # Product vision (if provided via prompts)
└── features/           # Empty features directory (created when first feature added)

# Also creates (if --interactive):
.specfact/config.yaml
```

### `specfact plan compare`

```bash
# Compare two bundles (explicit paths to bundle directories)
specfact plan compare \
  --manual .specfact/projects/manual-plan \
  --auto .specfact/projects/auto-derived \
  --out .specfact/reports/comparison/report-*.md

# Note: Commands accept bundle directory paths, not individual files
```

### `specfact sync bridge`

```bash
# Sync with external tools (Spec-Kit, Linear, Jira, etc.)
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional

# Watch mode
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch --interval 5

# Sync files are tracked in .specfact/reports/sync/
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

**See real examples**: [Integration Showcases](../examples/integration-showcases/) - 5 complete examples showing bugs fixed via IDE integrations

## Configuration File

`.specfact/config.yaml` (optional):

```yaml
version: "1.0"

# Default bundle to use (optional)
default_bundle: my-project

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
    ├── specfact.01-import.md
    ├── specfact.02-plan.md
    ├── specfact.03-review.md
    ├── specfact.04-sdd.md
    ├── specfact.05-enforce.md
    ├── specfact.06-sync.md
    ├── specfact.compare.md
    └── specfact.validate.md
```

### Example Structure (VS Code / Copilot)

```bash
.github/
└── prompts/
    ├── specfact.01-import.prompt.md
    ├── specfact.02-plan.prompt.md
    ├── specfact.03-review.prompt.md
    ├── specfact.04-sdd.prompt.md
    ├── specfact.05-enforce.prompt.md
    ├── specfact.06-sync.prompt.md
    ├── specfact.compare.prompt.md
    └── specfact.validate.prompt.md
.vscode/
└── settings.json  # Updated with promptFilesRecommendations
```

**Guidelines:**

- **Versioned** - IDE directories are typically committed to git (team-shared configuration)
- **Templates** - Prompt templates are read-only for the IDE, not modified by users
- **Settings** - VS Code `settings.json` is merged (not overwritten) to preserve existing settings
- **Auto-discovery** - IDEs automatically discover and register templates as slash commands
- **CLI-first** - Works offline, no account required, no vendor lock-in

**See [IDE Integration Guide](../guides/ide-integration.md)** for detailed setup and usage.

**See real examples**: [Integration Showcases](../examples/integration-showcases/) - 5 complete examples showing bugs fixed via IDE integrations

---

## SpecFact CLI Package Structure

The SpecFact CLI package includes prompt templates that are copied to IDE locations:

```bash
specfact-cli/
└── resources/
    └── prompts/              # Prompt templates (in package)
        ├── specfact.01-import.md
        ├── specfact.02-plan.md
        ├── specfact.03-review.md
        ├── specfact.04-sdd.md
        ├── specfact.05-enforce.md
        ├── specfact.06-sync.md
        ├── specfact.compare.md
        ├── specfact.validate.md
        └── shared/
            └── cli-enforcement.md
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
.specfact/projects/*/reports/
.specfact/projects/*/logs/
.specfact/cache/

# Keep these versioned
!.specfact/projects/
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
# Old structure (monolithic bundles, deprecated)
.specfact/plans/<name>.bundle.<format>
.specfact/reports/analysis.md

# New structure (modular bundles)
.specfact/projects/my-project/
├── bundle.manifest.yaml
└── bundle.yaml
.specfact/reports/brownfield/analysis.md

# Migration
mkdir -p .specfact/projects/my-project .specfact/reports/brownfield
# Convert monolithic bundle to modular bundle structure
# (Use 'specfact plan upgrade' or manual conversion)
mv reports/analysis.md .specfact/reports/brownfield/
```

## Multiple Plans in One Repository

SpecFact supports multiple plan bundles for:

- **Brownfield modernization** ⭐ **PRIMARY**: Separate plans for legacy components vs modernized code
- **Monorepos**: One plan per service
- **Feature branches**: Feature-specific plans

**Example (Brownfield Modernization)**:

```bash
.specfact/projects/
├── my-project/                      # Overall project bundle
│   ├── bundle.manifest.yaml
│   ├── product.yaml
│   └── features/
│       └── ...
├── legacy-api/                      # ⭐ Reverse-engineered from existing API (brownfield)
│   ├── bundle.manifest.yaml
│   ├── product.yaml
│   └── features/
│       ├── FEATURE-AUTH.yaml
│       └── FEATURE-API.yaml
├── legacy-payment/                  # ⭐ Reverse-engineered from existing payment system (brownfield)
│   ├── bundle.manifest.yaml
│   ├── product.yaml
│   └── features/
│       └── FEATURE-PAYMENT.yaml
├── modernized-api/                  # New API bundle (after modernization)
│   ├── bundle.manifest.yaml
│   ├── product.yaml
│   └── features/
│       └── ...
└── feature-new-auth/                # Experimental feature bundle
    ├── bundle.manifest.yaml
    ├── product.yaml
    └── features/
        └── FEATURE-AUTH.yaml
```

**Usage (Brownfield Workflow)**:

```bash
# Step 1: Reverse-engineer legacy codebase
specfact import from-code legacy-api \
  --repo src/legacy-api \
  --confidence 0.7

# Step 2: Compare legacy vs modernized (use bundle directories, not files)
specfact plan compare \
  --manual .specfact/projects/legacy-api \
  --auto .specfact/projects/modernized-api

# Step 3: Analyze specific legacy component
specfact import from-code legacy-payment \
  --repo src/legacy-payment \
  --confidence 0.7
```

## Summary

### SpecFact Artifacts

- **`.specfact/`** - All SpecFact artifacts live here
- **`projects/` and `protocols/`** - Versioned (git)
- **`reports/`, `gates/results/`, `cache/`** - Gitignored (ephemeral)
- **Modular bundles** - Each bundle in its own directory with manifest and content files
- **Use descriptive bundle names** - Supports multiple bundles per repo
- **Default paths always start with `.specfact/`** - Consistent and predictable
- **Timestamped reports** - Auto-generated reports include timestamps for tracking
- **Bridge architecture** - Bidirectional sync with external tools (Spec-Kit, Linear, Jira, etc.) via bridge adapters

### IDE Integration

- **IDE directories** - Created by `specfact init` (e.g., `.cursor/commands/`, `.github/prompts/`)
- **Prompt templates** - Copied from `resources/prompts/` in SpecFact CLI package
- **Typically versioned** - IDE directories are usually committed to git for team sharing
- **Auto-discovery** - IDEs automatically discover and register templates as slash commands
- **Settings files** - VS Code `settings.json` is merged (not overwritten)

### Quick Reference

| Type | Location | Git Status | Purpose |
|------|----------|------------|---------|
| **Project Bundles** | `.specfact/projects/<bundle-name>/` | Versioned | Modular contract definitions |
| **Bundle Prompts** | `.specfact/projects/<bundle-name>/prompts/` | Versioned (optional) | AI IDE contract enhancement prompts |
| **Protocols** | `.specfact/protocols/` | Versioned | FSM definitions |
| **Reports** | `.specfact/reports/` | Gitignored | Analysis reports |
| **Cache** | `.specfact/cache/` | Gitignored | Tool caches |
| **IDE Templates** | `.cursor/commands/`, `.github/prompts/`, etc. | Versioned (recommended) | Slash command templates |
