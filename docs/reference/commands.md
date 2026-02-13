---
layout: default
title: Command Reference
permalink: /reference/commands/
---

# Command Reference

Complete reference for all SpecFact CLI commands.

## Module-Aware Command Architecture

SpecFact command groups are implemented by lifecycle-managed modules.

- Core runtime owns lifecycle, registry, contracts, and orchestration.
- Feature command logic lives in module-local implementations.
- Legacy command imports are compatibility shims during migration.

Developer import/layout guidance:

- Primary implementations: `src/specfact_cli/modules/<module>/src/commands.py`
- Compatibility shims: `src/specfact_cli/commands/*.py` (only `app` re-export guaranteed)
- Preferred imports:
  - `from specfact_cli.modules.<module>.src.commands import app`
  - `from specfact_cli.modules.<module>.src.commands import <symbol>`

## Commands by Workflow

**Quick Navigation**: Find commands organized by workflow and command chain.

👉 **[Command Chains Reference](../guides/command-chains.md)** ⭐ **NEW** - Complete workflows with decision trees and visual diagrams

### Workflow Matrix

| Workflow | Primary Commands | Chain Reference |
|----------|-----------------|-----------------|
| **Brownfield Modernization** | `import from-code`, `plan review`, `plan update-feature`, `enforce sdd`, `repro` | [Brownfield Chain](../guides/command-chains.md#1-brownfield-modernization-chain) |
| **Greenfield Planning** | `plan init`, `plan add-feature`, `plan add-story`, `plan review`, `plan harden`, `generate contracts`, `enforce sdd` | [Greenfield Chain](../guides/command-chains.md#2-greenfield-planning-chain) |
| **External Tool Integration** | `import from-bridge`, `plan review`, `sync bridge`, `enforce sdd` | [Integration Chain](../guides/command-chains.md#3-external-tool-integration-chain) |
| **API Contract Development** | `spec validate`, `spec backward-compat`, `spec generate-tests`, `spec mock`, `contract verify` | [API Chain](../guides/command-chains.md#4-api-contract-development-chain) |
| **Sidecar Validation** | `validate sidecar init`, `validate sidecar run` | [Sidecar Chain](../guides/command-chains.md#5-sidecar-validation-chain) |
| **Plan Promotion & Release** | `plan review`, `enforce sdd`, `plan promote`, `project version bump` | [Promotion Chain](../guides/command-chains.md#6-plan-promotion--release-chain) |
| **Code-to-Plan Comparison** | `import from-code`, `plan compare`, `drift detect`, `sync repository` | [Comparison Chain](../guides/command-chains.md#7-code-to-plan-comparison-chain) |
| **AI-Assisted Enhancement** | `generate contracts-prompt`, `contracts-apply`, `contract coverage`, `repro` | [AI Enhancement Chain](../guides/command-chains.md#7-ai-assisted-code-enhancement-chain-emerging) |
| **Test Generation** | `generate test-prompt`, `spec generate-tests`, `pytest` | [Test Generation Chain](../guides/command-chains.md#8-test-generation-from-specifications-chain-emerging) |
| **Gap Discovery & Fixing** | `repro --verbose`, `generate fix-prompt`, `enforce sdd` | [Gap Discovery Chain](../guides/command-chains.md#9-gap-discovery--fixing-chain-emerging) |

**Not sure which workflow to use?** → [Command Chains Decision Tree](../guides/command-chains.md#when-to-use-which-chain)

---

## Quick Reference

### Most Common Commands

```bash
# PRIMARY: Import from existing code (brownfield modernization)
specfact import from-code legacy-api --repo .

# SECONDARY: Import from external tools (Spec-Kit, Linear, Jira, etc.)
specfact import from-bridge --repo . --adapter speckit --write

# Initialize plan (alternative: greenfield workflow)
specfact plan init legacy-api --interactive

# Compare plans
specfact plan compare --bundle legacy-api

# Sync with external tools (bidirectional) - Secondary use case
specfact sync bridge --adapter speckit --bundle legacy-api --bidirectional --watch

# Set up CrossHair for contract exploration (one-time setup)
specfact repro setup

# Validate everything
specfact repro --verbose

# Authenticate with DevOps providers (device code)
specfact auth github
specfact auth azure-devops
specfact auth status
```

### Global Flags

- `--input-format {yaml,json}` - Override default structured input detection for CLI commands (defaults to YAML)
- `--output-format {yaml,json}` - Control how plan bundles and reports are written (JSON is ideal for CI/copilot automations)
- `--interactive/--no-interactive` - Force prompt behavior (default auto-detection from terminal + CI environment)

### Commands by Workflow

**Import & Analysis:**

- `import from-code` ⭐ **PRIMARY** - Analyze existing codebase (brownfield modernization)
- `import from-bridge` - Import from external tools via bridge architecture (Spec-Kit, Linear, Jira, etc.)

**Plan Management:**

- `plan init <bundle-name>` - Initialize new project bundle
- `plan add-feature --bundle <bundle-name>` - Add feature to bundle
- `plan add-story --bundle <bundle-name>` - Add story to feature
- `plan update-feature --bundle <bundle-name>` - Update existing feature metadata
- `plan review <bundle-name>` - Review plan bundle to resolve ambiguities
- `plan select` - Select active plan from available bundles
- `plan upgrade` - Upgrade plan bundles to latest schema version
- `plan compare` - Compare plans (detect drift)

**Project Bundle Management:**

- `project init-personas` - Initialize persona definitions for team collaboration
  - **Workflow**: [Team Collaboration Workflow](../guides/team-collaboration-workflow.md)
- `project export --bundle <bundle-name> --persona <persona>` - Export persona-specific Markdown artifacts
  - **Workflow**: [Team Collaboration Workflow](../guides/team-collaboration-workflow.md), [Plan Promotion & Release Chain](../guides/command-chains.md#5-plan-promotion--release-chain)
- `project import --bundle <bundle-name> --persona <persona> --source <file>` - Import persona edits from Markdown
  - **Workflow**: [Team Collaboration Workflow](../guides/team-collaboration-workflow.md), [Plan Promotion & Release Chain](../guides/command-chains.md#5-plan-promotion--release-chain)
- `project lock --bundle <bundle-name> --section <section> --persona <persona>` - Lock section for editing
  - **Workflow**: [Team Collaboration Workflow](../guides/team-collaboration-workflow.md)
- `project unlock --bundle <bundle-name> --section <section>` - Unlock section after editing
  - **Workflow**: [Team Collaboration Workflow](../guides/team-collaboration-workflow.md)
- `project locks --bundle <bundle-name>` - List all locked sections
  - **Workflow**: [Team Collaboration Workflow](../guides/team-collaboration-workflow.md)
- `project version check --bundle <bundle-name>` - Recommend version bump (major/minor/patch/none)
  - **Workflow**: [Plan Promotion & Release Chain](../guides/command-chains.md#5-plan-promotion--release-chain)
- `project version bump --bundle <bundle-name> --type <major|minor|patch>` - Apply SemVer bump and record history
  - **Workflow**: [Plan Promotion & Release Chain](../guides/command-chains.md#5-plan-promotion--release-chain)
- `project version set --bundle <bundle-name> --version <semver>` - Set explicit project version and record history
  - **Workflow**: [Plan Promotion & Release Chain](../guides/command-chains.md#5-plan-promotion--release-chain)
- **CI/CD Integration**: The GitHub Action template includes a configurable version check step with three modes:
  - `info`: Informational only, logs recommendations without failing CI
  - `warn` (default): Logs warnings but continues CI execution
  - `block`: Fails CI if version bump recommendation is not followed
  Configure via `version_check_mode` input in workflow_dispatch or set `SPECFACT_VERSION_CHECK_MODE` environment variable.

**Enforcement:**

- `enforce sdd` - Validate SDD manifest compliance
  - **Workflow**: [Brownfield Modernization Chain](../guides/command-chains.md#1-brownfield-modernization-chain), [Greenfield Planning Chain](../guides/command-chains.md#2-greenfield-planning-chain), [Plan Promotion & Release Chain](../guides/command-chains.md#5-plan-promotion--release-chain)
- `enforce stage` - Configure quality gates
- `repro` - Run validation suite
  - **Workflow**: [Brownfield Modernization Chain](../guides/command-chains.md#1-brownfield-modernization-chain), [Gap Discovery & Fixing Chain](../guides/command-chains.md#9-gap-discovery--fixing-chain-emerging)
- `drift detect` - Detect drift between code and specifications
  - **Workflow**: [Code-to-Plan Comparison Chain](../guides/command-chains.md#6-code-to-plan-comparison-chain)

**AI IDE Bridge (v0.17+):**

- `generate fix-prompt` ⭐ **NEW** - Generate AI IDE prompt to fix gaps
- `generate test-prompt` ⭐ **NEW** - Generate AI IDE prompt to create tests
- `generate tasks` - ⚠️ **REMOVED in v0.22.0** - Use Spec-Kit, OpenSpec, or other SDD tools instead
- `generate contracts` - Generate contract stubs from SDD
- `generate contracts-prompt` - Generate AI IDE prompt for adding contracts

**Synchronization:**

- `sync bridge` - Sync with external tools via bridge architecture (Spec-Kit, Linear, Jira, etc.)
  - **Workflow**: [External Tool Integration Chain](../guides/command-chains.md#3-external-tool-integration-chain)
- `sync repository` - Sync code changes
  - **Workflow**: [Code-to-Plan Comparison Chain](../guides/command-chains.md#6-code-to-plan-comparison-chain)

**Validation & Quality:**

- `validate sidecar init` - Initialize sidecar workspace for validation
- `validate sidecar run` - Run sidecar validation workflow (CrossHair + Specmatic)
  - **Workflow**: [Sidecar Validation Chain](../guides/command-chains.md#5-sidecar-validation-chain)

**API Specification Management:**

- `spec validate` - Validate OpenAPI/AsyncAPI specifications with Specmatic
  - **Workflow**: [API Contract Development Chain](../guides/command-chains.md#4-api-contract-development-chain)
- `spec backward-compat` - Check backward compatibility between spec versions
  - **Workflow**: [API Contract Development Chain](../guides/command-chains.md#4-api-contract-development-chain)
- `spec generate-tests` - Generate contract tests from specifications
  - **Workflow**: [API Contract Development Chain](../guides/command-chains.md#4-api-contract-development-chain), [Test Generation from Specifications Chain](../guides/command-chains.md#8-test-generation-from-specifications-chain-emerging)
- `spec mock` - Launch mock server for development
  - **Workflow**: [API Contract Development Chain](../guides/command-chains.md#4-api-contract-development-chain)

**Constitution Management (Spec-Kit Compatibility):**

- `sdd constitution bootstrap` - Generate bootstrap constitution from repository analysis (for Spec-Kit format)
- `sdd constitution enrich` - Auto-enrich existing constitution with repository context (for Spec-Kit format)
- `sdd constitution validate` - Validate constitution completeness (for Spec-Kit format)

**Note**: The `sdd constitution` commands are for **Spec-Kit compatibility** only. SpecFact itself uses modular project bundles (`.specfact/projects/<bundle-name>/`) and protocols (`.specfact/protocols/*.protocol.yaml`) for internal operations. Constitutions are only needed when syncing with Spec-Kit artifacts or working in Spec-Kit format.

**⚠️ Breaking Change**: The `specfact bridge constitution` command has been moved to `specfact sdd constitution` as part of the bridge adapter refactoring. Please update your scripts and workflows.

**Migration & Utilities:**

- `migrate cleanup-legacy` - Remove empty legacy directories
- `migrate to-contracts` - Migrate bundles to contract-centric structure
- `migrate artifacts` - Migrate artifacts between bundle versions
- `sdd list` - List all SDD manifests in repository

**Setup & Maintenance:**

- `init` - Bootstrap CLI local state and manage enabled/disabled modules
- `init ide` - Initialize IDE prompt/template integration
- `upgrade` - Check for and install CLI updates

**⚠️ Deprecated (v0.17.0):**

- `implement tasks` - Use `generate fix-prompt` / `generate test-prompt` instead

---

## Global Options

```bash
specfact [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**

- `--version`, `-v` - Show version and exit
- `--help`, `-h` - Show help message and exit
- `--help-advanced`, `-ha` - Show all options including advanced configuration (progressive disclosure)
- `--no-banner` - Hide ASCII art banner (useful for CI/CD)
- `--debug` - Enable debug mode: show debug messages in the console and write them (plus structured operation metadata) to `~/.specfact/logs/specfact-debug.log`. See [Debug Logging](debug-logging.md).
- `--verbose` - Enable verbose output
- `--quiet` - Suppress non-error output
- `--mode {cicd|copilot}` - Operational mode (default: auto-detect)

**Mode Selection:**

- `cicd` - CI/CD automation mode (fast, deterministic)
- `copilot` - CoPilot-enabled mode (interactive, enhanced prompts)
- Auto-detection: Checks CoPilot API availability and IDE integration

**Boolean Flags:**

Boolean flags in SpecFact CLI work differently from value flags:

- ✅ **CORRECT**: `--flag` (sets True) or `--no-flag` (sets False) or omit (uses default)
- ❌ **WRONG**: `--flag true` or `--flag false` (Typer boolean flags don't accept values)

Examples:

- `--draft` sets draft status to True
- `--no-draft` sets draft status to False (when supported)
- Omitting the flag leaves the value unchanged (if optional) or uses the default

**Note**: Some boolean flags support `--no-flag` syntax (e.g., `--draft/--no-draft`), while others are simple presence flags (e.g., `--shadow-only`). Check command help with `specfact <command> --help` for specific flag behavior.

**Banner Display:**

The CLI shows a simple version line by default (e.g., `SpecFact CLI - v0.26.6`) for cleaner output. The full ASCII art banner is shown:

- On first run (when `~/.specfact` folder doesn't exist)
- When explicitly requested with `--banner` flag

To show the banner explicitly:

```bash
specfact --banner <command>
```

**Startup Performance:**

The CLI optimizes startup performance by:

- **Template checks**: Only run when CLI version has changed since last check (stored in `~/.specfact/metadata.json`)
- **Version checks**: Only run if >= 24 hours since last check (rate-limited to once per day)
- **Skip checks**: Use `--skip-checks` to disable all startup checks (useful for CI/CD)

This ensures fast startup times (< 2 seconds) while still providing important notifications when needed.

**Examples:**

```bash
# Auto-detect mode (default)
specfact import from-code legacy-api --repo .

# Force CI/CD mode
specfact --mode cicd import from-code legacy-api --repo .

# Force CoPilot mode
specfact --mode copilot import from-code legacy-api --repo .
```

## Commands

### `auth` - Authenticate with DevOps Providers

Authenticate to GitHub or Azure DevOps using device code flows and store tokens locally for adapter sync. See [Authentication](authentication.md) for full details.

```bash
specfact auth [COMMAND] [OPTIONS]
```

#### `auth github`

Authenticate to GitHub via device code flow (supports GitHub Enterprise).

```bash
specfact auth github [OPTIONS]
```

**Options:**

- `--client-id TEXT` - GitHub OAuth client ID (defaults to SpecFact GitHub App or `SPECFACT_GITHUB_CLIENT_ID`)
- `--base-url TEXT` - GitHub base URL (default: `https://github.com`, use your enterprise host)

**Examples:**

```bash
# Default GitHub device code flow
specfact auth github

# Custom OAuth app
specfact auth github --client-id YOUR_CLIENT_ID

# GitHub Enterprise
specfact auth github --base-url https://github.example.com
```

**Note:** The default client ID works only for `https://github.com`. For GitHub Enterprise, provide `--client-id` or set `SPECFACT_GITHUB_CLIENT_ID`.

#### `auth azure-devops`

Authenticate to Azure DevOps via device code flow.

```bash
specfact auth azure-devops
```

#### `auth status`

Show stored authentication tokens.

```bash
specfact auth status
```

#### `auth clear`

Clear stored authentication tokens.

```bash
# Clear one provider
specfact auth clear --provider github

# Clear all providers
specfact auth clear
```

**Options:**

- `--provider TEXT` - Provider to clear (`github` or `azure-devops`)

---

### `import` - Import from External Formats

Convert external project formats to SpecFact format.

#### `import from-bridge`

Convert external tool projects (code/spec adapters only) to SpecFact format using the bridge architecture.

**Note**: This command is for **code/spec adapters only** (Spec-Kit, OpenSpec, generic-markdown). For backlog adapters (GitHub Issues, ADO, Linear, Jira), use [`sync bridge`](#sync-bridge) instead.

```bash
specfact import from-bridge [OPTIONS]
```

**Options:**

- `--repo PATH` - Path to repository with external tool artifacts (required)
- `--dry-run` - Preview changes without writing files
- `--write` - Write converted files to repository
- `--out-branch NAME` - Git branch for migration (default: `feat/specfact-migration`)
- `--report PATH` - Write migration report to file
- `--force` - Overwrite existing files

**Advanced Options** (hidden by default, use `--help-advanced` or `-ha` to view):

- `--adapter ADAPTER` - Adapter type: `speckit`, `openspec`, `generic-markdown` (default: auto-detect)
  - **Code/Spec adapters**: `speckit`, `openspec`, `generic-markdown` - Use `import from-bridge`
  - **Backlog adapters**: `github`, `ado`, `linear`, `jira` - Use `sync bridge` instead (see [DevOps Adapter Integration](../guides/devops-adapter-integration.md))

**Example:**

```bash
# Import from Spec-Kit
specfact import from-bridge \
  --repo ./my-speckit-project \
  --adapter speckit \
  --write \
  --out-branch feat/specfact-migration \
  --report migration-report.md

# Auto-detect adapter
specfact import from-bridge \
  --repo ./my-project \
  --write
```

**What it does:**

- Uses bridge configuration to detect external tool structure
- For Spec-Kit: Detects `.specify/` directory with markdown artifacts in `specs/` folders
- Parses tool-specific artifacts (e.g., `specs/[###-feature-name]/spec.md`, `plan.md`, `tasks.md`, `.specify/memory/constitution.md` for Spec-Kit)
- Converts tool features/stories to SpecFact Pydantic models with contracts
- Generates `.specfact/protocols/workflow.protocol.yaml` (if FSM detected)
- Creates modular project bundle at `.specfact/projects/<bundle-name>/` with features and stories
- Adds Semgrep async anti-pattern rules (if async patterns detected)

---

#### `import from-code`

Import plan bundle from existing codebase (one-way import) using **AI-first approach** (CoPilot mode) or **AST-based fallback** (CI/CD mode).

```bash
specfact import from-code [OPTIONS]
```

**Options:**

- `BUNDLE_NAME` - Project bundle name (positional argument, required)
- `--repo PATH` - Path to repository to import (required)
- `--output-format {yaml,json}` - Override global output format for this command only (defaults to global flag)
- `--shadow-only` - Observe without blocking
- `--report PATH` - Write import report (default: bundle-specific `.specfact/projects/<bundle-name>/reports/brownfield/analysis-<timestamp>.md`, Phase 8.5)
- `--enrich-for-speckit/--no-enrich-for-speckit` - Automatically enrich plan for Spec-Kit compliance using PlanEnricher (enhances vague acceptance criteria, incomplete requirements, generic tasks, and adds edge case stories for features with only 1 story). Default: enabled (same enrichment logic as `plan review --auto-enrich`)

**Advanced Options** (hidden by default, use `--help-advanced` or `-ha` to view):

- `--confidence FLOAT` - Minimum confidence score (0.0-1.0, default: 0.5)
- `--key-format {classname|sequential}` - Feature key format (default: `classname`)
- `--entry-point PATH` - Subdirectory path for partial analysis (relative to repo root). Analyzes only files within this directory and subdirectories. Useful for:
  - **Multi-project repositories (monorepos)**: Analyze one project at a time (e.g., `--entry-point projects/api-service`)
  - **Large codebases**: Focus on specific modules or subsystems for faster analysis
  - **Incremental modernization**: Modernize one part of the codebase at a time
  - Example: `--entry-point src/core` analyzes only `src/core/` and its subdirectories
- `--enrichment PATH` - Path to Markdown enrichment report from LLM (applies missing features, confidence adjustments, business context). The enrichment report must follow a specific format (see [Dual-Stack Enrichment Guide](../guides/dual-stack-enrichment.md) for format requirements). When applied:
  - Missing features are added with their stories and acceptance criteria
  - Existing features are updated (confidence, outcomes, title if empty)
  - Stories are merged into existing features (new stories added, existing preserved)
  - Business context is applied to the plan bundle
- `--revalidate-features/--no-revalidate-features` - Re-validate and re-analyze existing features even if source files haven't changed. Useful when:
  - Analysis logic has improved and you want to re-analyze with better algorithms
  - Confidence threshold has changed and you want to re-evaluate features
  - Source files were modified outside the repository (e.g., moved, renamed)
  - Default: `False` (only re-analyze if files changed). When enabled, forces full codebase analysis regardless of incremental change detection

**Note**: The bundle name (positional argument) will be automatically sanitized (lowercased, spaces/special chars removed) for filesystem persistence. The bundle is created at `.specfact/projects/<bundle-name>/`.

**Mode Behavior:**

- **CoPilot Mode** (AI-first - Pragmatic): Uses AI IDE's native LLM (Cursor, CoPilot, etc.) for semantic understanding. The AI IDE understands the codebase semantically, then calls the SpecFact CLI for structured analysis. No separate LLM API setup needed. Multi-language support, high-quality Spec-Kit artifacts.

- **CI/CD Mode** (AST+Semgrep Hybrid): Uses Python AST + Semgrep pattern detection for fast, deterministic analysis. Framework-aware detection (API endpoints, models, CRUD, code quality). Works offline, no LLM required. Displays plugin status (AST Analysis, Semgrep Pattern Detection, Dependency Graph Analysis).

**Pragmatic Integration**:

- ✅ **No separate LLM setup** - Uses AI IDE's existing LLM
- ✅ **No additional API costs** - Leverages existing IDE infrastructure
- ✅ **Simpler architecture** - No langchain, API keys, or complex integration
- ✅ **Better developer experience** - Native IDE integration via slash commands

**Note**: The command automatically detects mode based on CoPilot API availability. Use `--mode` to override.

- `--mode {cicd|copilot}` - Operational mode (default: auto-detect)

**Examples:**

```bash
# Full repository analysis
specfact import from-code legacy-api \
  --repo ./my-project \
  --confidence 0.7 \
  --shadow-only \
  --report reports/analysis.md

# Partial analysis (analyze only specific subdirectory)
specfact import from-code core-module \
  --repo ./my-project \
  --entry-point src/core \
  --confidence 0.7

# Multi-project codebase (analyze one project at a time)
specfact import from-code api-service \
  --repo ./monorepo \
  --entry-point projects/api-service

# Re-validate existing features (force re-analysis even if files unchanged)
specfact import from-code legacy-api \
  --repo ./my-project \
  --revalidate-features

# Resume interrupted import (features are saved early as checkpoint)
# If import is cancelled, restart with same command - it will resume from checkpoint
specfact import from-code legacy-api --repo ./my-project
```

**What it does:**

- **AST Analysis**: Extracts classes, methods, imports, docstrings
- **Semgrep Pattern Detection**: Detects API endpoints, database models, CRUD operations, auth patterns, framework usage, code quality issues
- **Dependency Graph**: Builds module dependency graph (when pyan3 and networkx available)
- **Evidence-Based Confidence Scoring**: Systematically combines AST + Semgrep evidence for accurate confidence scores:
  - Framework patterns (API, models, CRUD) increase confidence
  - Test patterns increase confidence
  - Anti-patterns and security issues decrease confidence
- **Code Quality Assessment**: Identifies anti-patterns and security vulnerabilities
- **Plugin Status**: Displays which analysis tools are enabled and used
- **Optimized Bundle Size**: 81% reduction (18MB → 3.4MB, 5.3x smaller) via test pattern extraction to OpenAPI contracts
- **Acceptance Criteria**: Limited to 1-3 high-level items per story, detailed examples in contract files
- **Interruptible**: Press Ctrl+C during analysis to cancel immediately (all parallel operations support graceful cancellation)
- **Progress Reporting**: Real-time progress bars show:
  - Feature analysis progress (features discovered, themes detected)
  - Source file linking progress (features linked to source files)
  - Contract extraction progress (OpenAPI contracts generated)
- **Performance Optimizations**:
  - Pre-computes AST parsing and file hashes (5-15x faster for large codebases)
  - Caches function mappings to avoid repeated file parsing
  - Optimized for repositories with thousands of features (e.g., SQLAlchemy with 3000+ features)
- **Early Save Checkpoint**: Features are saved immediately after initial analysis, allowing you to resume if the process is interrupted during expensive operations (source tracking, contract extraction)
- **Feature Validation**: When loading existing bundles, automatically validates:
  - Source files still exist (detects orphaned features)
  - Feature structure is valid (detects incomplete features)
  - Reports validation issues with actionable tips
- **Contract Extraction**: Automatically extracts API contracts from function signatures, type hints, and validation logic:
  - Function parameters → Request schema (JSON Schema format)
  - Return types → Response schema
  - Validation logic → Preconditions and postconditions
  - Error handling → Error contracts
  - Contracts stored in `Story.contracts` field for runtime enforcement
  - Contracts included in Spec-Kit plan.md for Article IX compliance
- **Test Pattern Extraction**: Extracts test patterns from existing test files:
  - Parses pytest and unittest test functions
  - Converts test assertions to Given/When/Then acceptance criteria format
  - Maps test scenarios to user story scenarios
- **Control Flow Analysis**: Extracts scenarios from code control flow:
  - Primary scenarios (happy path)
  - Alternate scenarios (conditional branches)
  - Exception scenarios (error handling)
  - Recovery scenarios (retry logic)
- **Requirement Extraction**: Extracts complete requirements from code semantics:
  - Subject + Modal + Action + Object + Outcome format
  - Non-functional requirements (NFRs) from code patterns
  - Performance, security, reliability, maintainability patterns
- Generates plan bundle with enhanced confidence scores

**Partial Repository Coverage:**

The `--entry-point` parameter enables partial analysis of large codebases:

- **Multi-project codebases**: Analyze individual projects within a monorepo separately
- **Focused analysis**: Analyze specific modules or subdirectories for faster feedback
- **Incremental modernization**: Modernize one module at a time, creating separate plan bundles per module
- **Performance**: Faster analysis when you only need to understand a subset of the codebase

**Note on Multi-Project Codebases:**

When working with multiple projects in a single repository, external tool integration (via `sync bridge`) may create artifacts at nested folder levels. For now, it's recommended to:

- Use `--entry-point` to analyze each project separately
- Create separate project bundles for each project (`.specfact/projects/<bundle-name>/`)
- Run `specfact init ide` from the repository root to ensure IDE integration works correctly (templates are copied to root-level `.github/`, `.cursor/`, etc. directories)

---

### `plan` - Manage Development Plans

Create and manage contract-driven development plans.

> Plan commands respect both `.bundle.yaml` and `.bundle.json`. Use `--output-format {yaml,json}` (or the global `specfact --output-format`) to control serialization.

#### `plan init`

Initialize a new plan bundle:

```bash
specfact plan init [OPTIONS]
```

**Options:**

- `--interactive/--no-interactive` - Interactive mode with prompts (default: `--interactive`)
  - Use `--no-interactive` for CI/CD automation to avoid interactive prompts
- Bundle name is provided as a positional argument (e.g., `plan init my-project`)
- `--scaffold/--no-scaffold` - Create complete `.specfact/` directory structure (default: `--scaffold`)
- `--output-format {yaml,json}` - Override global output format for this command only (defaults to global flag)

**Example:**

```bash
# Interactive mode (recommended for manual plan creation)
specfact plan init legacy-api --interactive

# Non-interactive mode (CI/CD automation)
specfact plan init legacy-api --no-interactive

# Interactive mode with different bundle
specfact plan init feature-auth --interactive
```

#### `plan add-feature`

Add a feature to the plan:

```bash
specfact plan add-feature [OPTIONS]
```

**Options:**

- `--key TEXT` - Feature key (FEATURE-XXX) (required)
- `--title TEXT` - Feature title (required)
- `--outcomes TEXT` - Success outcomes (multiple allowed)
- `--acceptance TEXT` - Acceptance criteria (multiple allowed)
- `--bundle TEXT` - Bundle name (default: active bundle or `main`)

**Example:**

```bash
specfact plan add-feature \
  --bundle legacy-api \
  --key FEATURE-001 \
  --title "Spec-Kit Import" \
  --outcomes "Zero manual conversion" \
  --acceptance "Given Spec-Kit repo, When import, Then bundle created"
```

#### `plan add-story`

Add a story to a feature:

```bash
specfact plan add-story [OPTIONS]
```

**Options:**

- `--feature TEXT` - Parent feature key (required)
- `--key TEXT` - Story key (e.g., STORY-001) (required)
- `--title TEXT` - Story title (required)
- `--acceptance TEXT` - Acceptance criteria (comma-separated)
- `--story-points INT` - Story points (complexity: 0-100)
- `--value-points INT` - Value points (business value: 0-100)
- `--draft` - Mark story as draft
- `--bundle TEXT` - Bundle name (default: active bundle or `main`)

**Example:**

```bash
specfact plan add-story \
  --bundle legacy-api \
  --feature FEATURE-001 \
  --key STORY-001 \
  --title "Parse Spec-Kit artifacts" \
  --acceptance "Schema validation passes"
```

#### `plan update-feature`

Update an existing feature's metadata in a plan bundle:

```bash
specfact plan update-feature [OPTIONS]
```

**Options:**

- `--key TEXT` - Feature key to update (e.g., FEATURE-001) (required unless `--batch-updates` is provided)
- `--title TEXT` - Feature title
- `--outcomes TEXT` - Expected outcomes (comma-separated)
- `--acceptance TEXT` - Acceptance criteria (comma-separated)
- `--constraints TEXT` - Constraints (comma-separated)
- `--confidence FLOAT` - Confidence score (0.0-1.0)
- `--draft/--no-draft` - Mark as draft (use `--draft` to set True, `--no-draft` to set False, omit to leave unchanged)
  - **Note**: Boolean flags don't accept values - use `--draft` (not `--draft true`) or `--no-draft` (not `--draft false`)
- `--batch-updates PATH` - Path to JSON/YAML file with multiple feature updates (preferred for bulk updates via Copilot LLM enrichment)
  - **File format**: List of objects with `key` and update fields (title, outcomes, acceptance, constraints, confidence, draft)
  - **Example file** (`updates.json`):

    ```json
    [
      {
        "key": "FEATURE-001",
        "title": "Updated Feature 1",
        "outcomes": ["Outcome 1", "Outcome 2"],
        "acceptance": ["Acceptance 1", "Acceptance 2"],
        "confidence": 0.9
      },
      {
        "key": "FEATURE-002",
        "title": "Updated Feature 2",
        "acceptance": ["Acceptance 3"],
        "confidence": 0.85
      }
    ]
    ```

- `--bundle TEXT` - Bundle name (default: active bundle or `main`)

**Example:**

```bash
# Single feature update
specfact plan update-feature \
  --bundle legacy-api \
  --key FEATURE-001 \
  --title "Updated Feature Title" \
  --outcomes "Outcome 1, Outcome 2"

# Update acceptance criteria and confidence
specfact plan update-feature \
  --bundle legacy-api \
  --key FEATURE-001 \
  --acceptance "Criterion 1, Criterion 2" \
  --confidence 0.9

# Batch updates from file (preferred for multiple features)
specfact plan update-feature \
  --bundle legacy-api \
  --batch-updates updates.json

# Batch updates with YAML format
specfact plan update-feature \
  --bundle main \
  --batch-updates updates.yaml
```

**Batch Update File Format:**

The `--batch-updates` file must contain a list of update objects. Each object must have a `key` field and can include any combination of update fields:

```json
[
  {
    "key": "FEATURE-001",
    "title": "Updated Feature 1",
    "outcomes": ["Outcome 1", "Outcome 2"],
    "acceptance": ["Acceptance 1", "Acceptance 2"],
    "constraints": ["Constraint 1"],
    "confidence": 0.9,
    "draft": false
  },
  {
    "key": "FEATURE-002",
    "title": "Updated Feature 2",
    "acceptance": ["Acceptance 3"],
    "confidence": 0.85
  }
]
```

**When to Use Batch Updates:**

- **Multiple features need refinement**: After plan review identifies multiple features with missing information
- **Copilot LLM enrichment**: When LLM generates comprehensive updates for multiple features at once
- **Bulk acceptance criteria updates**: When enhancing multiple features with specific file paths, method names, or component references
- **CI/CD automation**: When applying multiple updates programmatically from external tools

**What it does:**

- Updates existing feature metadata (title, outcomes, acceptance criteria, constraints, confidence, draft status)
- Works in CI/CD, Copilot, and interactive modes
- Validates plan bundle structure after update
- Preserves existing feature data (only updates specified fields)

**Use cases:**

- **After enrichment**: Update features added via enrichment that need metadata completion
- **CI/CD automation**: Update features programmatically in non-interactive environments
- **Copilot mode**: Update features without needing internal code knowledge

#### `plan update-story`

Update an existing story's metadata in a plan bundle:

```bash
specfact plan update-story [OPTIONS]
```

**Options:**

- `--feature TEXT` - Parent feature key (e.g., FEATURE-001) (required unless `--batch-updates` is provided)
- `--key TEXT` - Story key to update (e.g., STORY-001) (required unless `--batch-updates` is provided)
- `--title TEXT` - Story title
- `--acceptance TEXT` - Acceptance criteria (comma-separated)
- `--story-points INT` - Story points (complexity: 0-100)
- `--value-points INT` - Value points (business value: 0-100)
- `--confidence FLOAT` - Confidence score (0.0-1.0)
- `--draft/--no-draft` - Mark as draft (use `--draft` to set True, `--no-draft` to set False, omit to leave unchanged)
  - **Note**: Boolean flags don't accept values - use `--draft` (not `--draft true`) or `--no-draft` (not `--draft false`)
- `--batch-updates PATH` - Path to JSON/YAML file with multiple story updates (preferred for bulk updates via Copilot LLM enrichment)
  - **File format**: List of objects with `feature`, `key` and update fields (title, acceptance, story_points, value_points, confidence, draft)
  - **Example file** (`story_updates.json`):

    ```json
    [
      {
        "feature": "FEATURE-001",
        "key": "STORY-001",
        "title": "Updated Story 1",
        "acceptance": ["Given X, When Y, Then Z"],
        "story_points": 5,
        "value_points": 3,
        "confidence": 0.9
      },
      {
        "feature": "FEATURE-002",
        "key": "STORY-002",
        "acceptance": ["Given A, When B, Then C"],
        "confidence": 0.85
      }
    ]
    ```

- `--bundle TEXT` - Bundle name (default: active bundle or `main`)

**Example:**

```bash
# Single story update
specfact plan update-story \
  --feature FEATURE-001 \
  --key STORY-001 \
  --title "Updated Story Title" \
  --acceptance "Given X, When Y, Then Z"

# Update story points and confidence
specfact plan update-story \
  --feature FEATURE-001 \
  --key STORY-001 \
  --story-points 5 \
  --confidence 0.9

# Batch updates from file (preferred for multiple stories)
specfact plan update-story \
  --bundle main \
  --batch-updates story_updates.json

# Batch updates with YAML format
specfact plan update-story \
  --bundle main \
  --batch-updates story_updates.yaml
```

**Batch Update File Format:**

The `--batch-updates` file must contain a list of update objects. Each object must have `feature` and `key` fields and can include any combination of update fields:

```json
[
  {
    "feature": "FEATURE-001",
    "key": "STORY-001",
    "title": "Updated Story 1",
    "acceptance": ["Given X, When Y, Then Z"],
    "story_points": 5,
    "value_points": 3,
    "confidence": 0.9,
    "draft": false
  },
  {
    "feature": "FEATURE-002",
    "key": "STORY-002",
    "acceptance": ["Given A, When B, Then C"],
    "confidence": 0.85
  }
]
```

**When to Use Batch Updates:**

- **Multiple stories need refinement**: After plan review identifies multiple stories with missing information
- **Copilot LLM enrichment**: When LLM generates comprehensive updates for multiple stories at once
- **Bulk acceptance criteria updates**: When enhancing multiple stories with specific file paths, method names, or component references
- **CI/CD automation**: When applying multiple updates programmatically from external tools

**What it does:**

- Updates existing story metadata (title, acceptance criteria, story points, value points, confidence, draft status)
- Works in CI/CD, Copilot, and interactive modes
- Validates plan bundle structure after update
- Preserves existing story data (only updates specified fields)

#### `plan review`

Review plan bundle to identify and resolve ambiguities:

```bash
specfact plan review [OPTIONS]
```

**Options:**

- `--bundle TEXT` - Project bundle name (required, e.g., `legacy-api`)
- `--list-questions` - Output questions in JSON format without asking (for Copilot mode)
- `--output-questions PATH` - Save questions directly to file (JSON format). Use with `--list-questions` to save instead of stdout. Default: None
- `--list-findings` - Output all findings in structured format (JSON/YAML) or as table (interactive mode). Preferred for bulk updates via Copilot LLM enrichment
- `--output-findings PATH` - Save findings directly to file (JSON/YAML format). Use with `--list-findings` to save instead of stdout. Default: None
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--auto-enrich` - Automatically enrich vague acceptance criteria, incomplete requirements, and generic tasks using LLM-enhanced pattern matching

**Advanced Options** (hidden by default, use `--help-advanced` or `-ha` to view):

- `--max-questions INT` - Maximum questions per session (default: 5, max: 10)
- `--category TEXT` - Focus on specific taxonomy category (optional)
- `--findings-format {json,yaml,table}` - Output format for `--list-findings` (default: json for non-interactive, table for interactive)
- `--answers PATH|JSON` - JSON file path or JSON string with question_id -> answer mappings (for non-interactive mode)

**Modes:**

- **Interactive Mode**: Asks questions one at a time, integrates answers immediately
- **Copilot Mode**: Three-phase workflow:
  1. Get findings: `specfact plan review --list-findings --findings-format json` (preferred for bulk updates)
  2. LLM enrichment: Analyze findings and generate batch update files
  3. Apply updates: `specfact plan update-feature --batch-updates <file>` or `specfact plan update-story --batch-updates <file>`
- **Alternative Copilot Mode**: Question-based workflow:
  1. Get questions: `specfact plan review --list-questions`
  2. Ask user: LLM presents questions and collects answers
  3. Feed answers: `specfact plan review --answers <file>`
- **CI/CD Mode**: Use `--no-interactive` with `--answers` for automation

**Example:**

```bash
# Interactive review
specfact plan review legacy-api

# Get all findings for bulk updates (preferred for Copilot mode)
specfact plan review legacy-api --list-findings --findings-format json

# Save findings directly to file (clean JSON, no CLI banner)
specfact plan review legacy-api --list-findings --output-findings /tmp/findings.json

# Get findings as table (interactive mode)
specfact plan review legacy-api --list-findings --findings-format table

# Get questions for question-based workflow
specfact plan review legacy-api --list-questions --max-questions 5

# Save questions directly to file (clean JSON, no CLI banner)
specfact plan review legacy-api --list-questions --output-questions /tmp/questions.json

# Feed answers back (question-based workflow)
specfact plan review legacy-api --answers answers.json

# CI/CD automation
specfact plan review legacy-api --no-interactive --answers answers.json
```

**Findings Output Format:**

The `--list-findings` option outputs all ambiguities and findings in a structured format:

```json
{
  "findings": [
    {
      "category": "Feature/Story Completeness",
      "status": "Missing",
      "description": "Feature FEATURE-001 has no stories",
      "impact": 0.9,
      "uncertainty": 0.8,
      "priority": 0.72,
      "question": "What stories should be added to FEATURE-001?",
      "related_sections": ["features[0]"]
    }
  ],
  "coverage": {
    "Functional Scope & Behavior": "Missing",
    "Feature/Story Completeness": "Missing"
  },
  "total_findings": 5,
  "priority_score": 0.65
}
```

**Bulk Update Workflow (Recommended for Copilot Mode):**

1. **List findings**: `specfact plan review --list-findings --output-findings /tmp/findings.json` (recommended - clean JSON) or `specfact plan review --list-findings --findings-format json > findings.json` (includes CLI banner)
2. **LLM analyzes findings**: Generate batch update files based on findings
3. **Apply feature updates**: `specfact plan update-feature --batch-updates feature_updates.json`
4. **Apply story updates**: `specfact plan update-story --batch-updates story_updates.json`
5. **Verify**: Run `specfact plan review` again to confirm improvements

**What it does:**

1. **Analyzes** plan bundle for ambiguities using structured taxonomy (10 categories)
2. **Identifies** missing information, unclear requirements, and unknowns
3. **Asks** targeted questions (max 5 per session) to resolve ambiguities
4. **Integrates** answers back into plan bundle incrementally
5. **Validates** plan bundle structure after each update
6. **Reports** coverage summary and promotion readiness

**Taxonomy Categories:**

- Functional Scope & Behavior
- Domain & Data Model
- Interaction & UX Flow
- Non-Functional Quality Attributes
- Integration & External Dependencies
- Edge Cases & Failure Handling
- Constraints & Tradeoffs
- Terminology & Consistency
- Completion Signals
- Feature/Story Completeness

**Answers Format:**

The `--answers` parameter accepts either a JSON file path or JSON string:

```json
{
  "Q001": "Answer for question 1",
  "Q002": "Answer for question 2"
}
```

**Integration Points:**

Answers are integrated into plan bundle sections based on category:

- Functional ambiguity → `features[].acceptance[]` or `idea.narrative`
- Data model → `features[].constraints[]`
- Non-functional → `features[].constraints[]` or `idea.constraints[]`
- Edge cases → `features[].acceptance[]` or `stories[].acceptance[]`

**SDD Integration:**

When an SDD manifest (`.specfact/projects/<bundle-name>/sdd.yaml`, Phase 8.5) is present, `plan review` automatically:

- **Validates SDD manifest** against the plan bundle (hash match, coverage thresholds)
- **Displays contract density metrics**:
  - Contracts per story (compared to threshold)
  - Invariants per feature (compared to threshold)
  - Architecture facets (compared to threshold)
- **Reports coverage threshold warnings** if metrics are below thresholds
- **Suggests running** `specfact enforce sdd` for detailed validation report

**Example Output with SDD:**

```bash
✓ SDD manifest validated successfully

Contract Density Metrics:
  Contracts/story: 1.50 (threshold: 1.0)
  Invariants/feature: 2.00 (threshold: 1.0)
  Architecture facets: 3 (threshold: 3)

Found 0 coverage threshold warning(s)
```

**Output:**

- Questions asked count
- Sections touched (integration points)
- Coverage summary (per category status)
- Contract density metrics (if SDD present)
- Next steps (promotion readiness)

#### `plan harden`

Create or update SDD manifest (hard spec) from plan bundle:

```bash
specfact plan harden [OPTIONS]
```

**Options:**

- Bundle name is provided as a positional argument (e.g., `plan harden my-project`)
- `--sdd PATH` - Output SDD manifest path (default: bundle-specific `.specfact/projects/<bundle-name>/sdd.<format>`, Phase 8.5)
- `--output-format {yaml,json}` - SDD manifest format (defaults to global `--output-format`)
- `--interactive/--no-interactive` - Interactive mode with prompts (default: interactive)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)

**What it does:**

1. **Loads plan bundle** and computes content hash
2. **Extracts SDD sections** from plan bundle:
   - **WHY**: Intent, constraints, target users, value hypothesis (from `idea` section)
   - **WHAT**: Capabilities, acceptance criteria, out-of-scope (from `features` section)
   - **HOW**: Architecture, invariants, contracts, module boundaries (from `features` and `stories`)
3. **Creates SDD manifest** with:
   - Plan bundle linkage (hash and ID)
   - Coverage thresholds (contracts per story, invariants per feature, architecture facets)
   - Enforcement budgets (shadow, warn, block time limits)
   - Promotion status (from plan bundle stage)
4. **Saves plan bundle** with updated hash (ensures hash persists for subsequent commands)
5. **Saves SDD manifest** to `.specfact/projects/<bundle-name>/sdd.<format>` (bundle-specific, Phase 8.5)

**Important Notes:**

- **SDD-Plan Linkage**: SDD manifests are linked to specific plan bundles via hash
- **Multiple Plans**: Each bundle has its own SDD manifest in `.specfact/projects/<bundle-name>/sdd.yaml` (Phase 8.5)
- **Hash Persistence**: Plan bundle is automatically saved with updated hash to ensure consistency

**Example:**

```bash
# Interactive with active plan
specfact plan harden --bundle legacy-api

# Non-interactive with specific bundle
specfact plan harden --bundle legacy-api --no-interactive

# Custom SDD path for multiple bundles
specfact plan harden --bundle feature-auth  # SDD saved to .specfact/projects/feature-auth/sdd.yaml
```

**SDD Manifest Structure:**

The generated SDD manifest includes:

- `version`: Schema version (1.0.0)
- `plan_bundle_id`: First 16 characters of plan hash
- `plan_bundle_hash`: Full plan bundle content hash
- `why`: Intent, constraints, target users, value hypothesis
- `what`: Capabilities, acceptance criteria, out-of-scope
- `how`: Architecture description, invariants, contracts, module boundaries
- `coverage_thresholds`: Minimum contracts/story, invariants/feature, architecture facets
- `enforcement_budget`: Time budgets for shadow/warn/block enforcement levels
- `promotion_status`: Current plan bundle stage

#### `plan promote`

Promote a plan bundle through development stages with quality gate validation:

```bash
specfact plan promote <bundle-name> [OPTIONS]
```

**Arguments:**

- `<bundle-name>` - Project bundle name (required, positional argument, e.g., `legacy-api`)

**Options:**

- `--stage TEXT` - Target stage (draft, review, approved, released) (required)
- `--validate/--no-validate` - Run validation before promotion (default: true)
- `--force` - Force promotion even if validation fails (default: false)

**Stages:**

- **draft**: Initial state - can be modified freely
- **review**: Plan is ready for review - should be stable
- **approved**: Plan approved for implementation
- **released**: Plan released and should be immutable

**Example:**

```bash
# Promote to review stage
specfact plan promote legacy-api --stage review

# Promote to approved with validation
specfact plan promote legacy-api --stage approved --validate

# Force promotion (bypasses validation)
specfact plan promote legacy-api --stage released --force
```

**What it does:**

1. **Validates promotion rules**:
   - **Draft → Review**: All features must have at least one story
   - **Review → Approved**: All features and stories must have acceptance criteria
   - **Approved → Released**: Implementation verification (future check)

2. **Checks coverage status** (when `--validate` is enabled):
   - **Critical categories** (block promotion if Missing):
     - Functional Scope & Behavior
     - Feature/Story Completeness
     - Constraints & Tradeoffs
   - **Important categories** (warn if Missing or Partial):
     - Domain & Data Model
     - Integration & External Dependencies
     - Non-Functional Quality Attributes

3. **Updates metadata**: Sets stage, `promoted_at` timestamp, and `promoted_by` user

4. **Saves plan bundle** with updated metadata

**Coverage Validation:**

The promotion command now validates coverage status to ensure plans are complete before promotion:

- **Blocks promotion** if critical categories are Missing (unless `--force`)
- **Warns and prompts** if important categories are Missing or Partial (unless `--force`)
- **Suggests** running `specfact plan review` to resolve missing categories

**Validation Errors:**

If promotion fails due to validation:

```bash
❌ Cannot promote to review: 1 critical category(ies) are Missing
Missing critical categories:
  - Constraints & Tradeoffs

Run 'specfact plan review' to resolve these ambiguities
```

**Use `--force` to bypass** (not recommended):

```bash
specfact plan promote legacy-api --stage review --force
```

**Next Steps:**

After successful promotion, the CLI suggests next actions:

- **draft → review**: Review plan bundle, add stories if missing
- **review → approved**: Plan is ready for implementation
- **approved → released**: Plan is released and should be immutable

#### `plan select`

Select active plan from available plan bundles:

```bash
specfact plan select [PLAN] [OPTIONS]
```

**Arguments:**

- `PLAN` - Plan name or number to select (optional, for interactive selection)

**Options:**

- `PLAN` - Plan name or number to select (optional, for interactive selection)
- `--no-interactive` - Non-interactive mode (for CI/CD automation). Disables interactive prompts. Requires exactly one plan to match filters.

**Advanced Options** (hidden by default, use `--help-advanced` or `-ha` to view):

- `--current` - Show only the currently active plan (auto-selects in non-interactive mode)
- `--stages STAGES` - Filter by stages (comma-separated: `draft,review,approved,released`)
- `--last N` - Show last N plans by modification time (most recent first)
- `--name NAME` - Select plan by exact filename (non-interactive, e.g., `main.bundle.yaml`)
- `--id HASH` - Select plan by content hash ID (non-interactive, from metadata.summary.content_hash)

**Example:**

```bash
# Interactive selection (displays numbered list)
specfact plan select

# Select by number
specfact plan select 1

# Select by name
specfact plan select main.bundle.yaml

# Show only active plan
specfact plan select --current

# Filter by stages
specfact plan select --stages draft,review

# Show last 5 plans
specfact plan select --last 5

# CI/CD: Get active plan without prompts (auto-selects)
specfact plan select --no-interactive --current

# CI/CD: Get most recent plan without prompts
specfact plan select --no-interactive --last 1

# CI/CD: Select by exact filename
specfact plan select --name main.bundle.yaml

# CI/CD: Select by content hash ID
specfact plan select --id abc123def456
```

**What it does:**

- Lists all available plan bundles in `.specfact/projects/` with metadata (features, stories, stage, modified date)
- Displays numbered list with active plan indicator
- Applies filters (current, stages, last N) before display/selection
- Updates `.specfact/config.yaml` to set the active bundle (Phase 8.5: migrated from `.specfact/plans/config.yaml`)
- The active plan becomes the default for all commands with `--bundle` option:
  - **Plan management**: `plan compare`, `plan promote`, `plan add-feature`, `plan add-story`, `plan update-idea`, `plan update-feature`, `plan update-story`, `plan review`
  - **Analysis & generation**: `import from-code`, `generate contracts`, `analyze contracts`
  - **Synchronization**: `sync bridge`, `sync intelligent`
  - **Enforcement & migration**: `enforce sdd`, `migrate to-contracts`, `drift detect`
  
  Use `--bundle <name>` to override the active plan for any command.

**Filter Options:**

- `--current`: Filters to show only the currently active plan. In non-interactive mode, automatically selects the active plan without prompts.
- `--stages`: Filters plans by stage (e.g., `--stages draft,review` shows only draft and review plans)
- `--last N`: Shows the N most recently modified plans (sorted by modification time, most recent first)
- `--name NAME`: Selects plan by exact filename (non-interactive). Useful for CI/CD when you know the exact plan name.
- `--id HASH`: Selects plan by content hash ID from `metadata.summary.content_hash` (non-interactive). Supports full hash or first 8 characters.
- `--no-interactive`: Disables interactive prompts. If multiple plans match filters, command will error. Use with `--current`, `--last 1`, `--name`, or `--id` for single plan selection in CI/CD.

**Performance Notes:**

The `plan select` command uses optimized metadata reading for fast performance, especially with large plan bundles:

- Plan bundles include summary metadata (features count, stories count, content hash) at the top of the file
- For large files (>10MB), only the metadata section is read (first 50KB)
- This provides 44% faster performance compared to full file parsing
- Summary metadata is automatically added when creating or upgrading plan bundles

**Note**: Project bundles are stored in `.specfact/projects/<bundle-name>/`. All plan commands (`compare`, `promote`, `add-feature`, `add-story`) use the bundle name specified via `--bundle` option or positional arguments.

#### `plan sync`

Enable shared plans for team collaboration (convenience wrapper for `sync bridge --adapter speckit --bidirectional`):

```bash
specfact plan sync --shared [OPTIONS]
```

**Options:**

- `--shared` - Enable shared plans (bidirectional sync for team collaboration)
- `--watch` - Watch mode for continuous sync (monitors file changes in real-time)
- `--interval INT` - Watch interval in seconds (default: 5, minimum: 1)
- `--repo PATH` - Path to repository (default: `.`)
- `--bundle BUNDLE_NAME` - Project bundle name for SpecFact → tool conversion (default: auto-detect)
- `--overwrite` - Overwrite existing tool artifacts (delete all existing before sync)

**Shared Plans for Team Collaboration:**

The `plan sync --shared` command is a convenience wrapper around `sync bridge --adapter speckit --bidirectional` that emphasizes team collaboration. **Shared structured plans** enable multiple developers to work on the same plan with automated bidirectional sync. Unlike Spec-Kit's manual markdown sharing, SpecFact automatically keeps plans synchronized across team members.

**Example:**

```bash
# One-time shared plans sync
specfact plan sync --shared

# Continuous watch mode (recommended for team collaboration)
specfact plan sync --shared --watch --interval 5

# Sync specific repository and bundle
specfact plan sync --shared --repo ./project --bundle my-project

# Equivalent direct command:
specfact sync bridge --adapter speckit --repo . --bundle my-project --bidirectional --watch
```

**What it syncs:**

- **Tool → SpecFact**: New `spec.md`, `plan.md`, `tasks.md` → Updated `.specfact/projects/<bundle-name>/bundle.yaml`
- **SpecFact → Tool**: Changes to `.specfact/projects/<bundle-name>/bundle.yaml` → Updated tool markdown (preserves structure)
- **Team collaboration**: Multiple developers can work on the same plan with automated synchronization

**Note**: This is a convenience wrapper. The underlying command is `sync bridge --adapter speckit --bidirectional`. See [`sync bridge`](#sync-bridge) for full details.

#### `plan upgrade`

Upgrade plan bundles to the latest schema version:

```bash
specfact plan upgrade [OPTIONS]
```

**Options:**

- `--plan PATH` - Path to specific plan bundle to upgrade (default: active plan from `specfact plan select`)
- `--all` - Upgrade all project bundles in `.specfact/projects/`
- `--dry-run` - Show what would be upgraded without making changes

**Example:**

```bash
# Preview what would be upgraded (active plan)
specfact plan upgrade --dry-run

# Upgrade active plan (uses bundle selected via `specfact plan select`)
specfact plan upgrade

# Upgrade specific plan by path
specfact plan upgrade --plan .specfact/projects/my-project/bundle.manifest.yaml

# Upgrade all plans
specfact plan upgrade --all

# Preview all upgrades
specfact plan upgrade --all --dry-run
```

**What it does:**

- Detects plan bundles with older schema versions or missing summary metadata
- Migrates plan bundles from older versions to the current version (1.1)
- Adds summary metadata (features count, stories count, content hash) for performance optimization
- Preserves all existing plan data while adding new fields
- Updates plan bundle version to current schema version

**Schema Versions:**

- **Version 1.0**: Initial schema (no summary metadata)
- **Version 1.1**: Added summary metadata for fast access without full parsing

**When to use:**

- After upgrading SpecFact CLI to a version with new schema features
- When you notice slow performance with `plan select` (indicates missing summary metadata)
- Before running batch operations on multiple plan bundles
- As part of repository maintenance to ensure all plans are up to date

**Migration Details:**

The upgrade process:

1. Detects schema version from plan bundle's `version` field
2. Checks for missing summary metadata (backward compatibility)
3. Applies migrations in sequence (supports multi-step migrations)
4. Computes and adds summary metadata with content hash for integrity verification
5. Updates plan bundle file with new schema version

**Active Plan Detection:**

When no `--plan` option is provided, the command automatically uses the active bundle set via `specfact plan select`. If no active bundle is set, it falls back to the first available bundle in `.specfact/projects/` and provides a helpful tip to set it as active.

**Backward Compatibility:**

- Older bundles (schema 1.0) missing the `product` field are automatically upgraded with default empty `product` structure
- Missing required fields are provided with sensible defaults during migration
- Upgraded plan bundles are backward compatible. Older CLI versions can still read them, but won't benefit from performance optimizations

#### `plan compare`

Compare manual and auto-derived plans to detect code vs plan drift:

```bash
specfact plan compare [OPTIONS]
```

**Options:**

- `--manual PATH` - Manual plan bundle directory (intended design - what you planned) (default: active bundle from `.specfact/projects/<bundle-name>/` or `main`)
- `--auto PATH` - Auto-derived plan bundle directory (actual implementation - what's in your code from `import from-code`) (default: latest in `.specfact/projects/`)
- `--code-vs-plan` - Convenience alias for `--manual <active-plan> --auto <latest-auto-plan>` (detects code vs plan drift)
- `--output-format TEXT` - Output format (markdown, json, yaml) (default: markdown)
- `--out PATH` - Output file (default: bundle-specific `.specfact/projects/<bundle-name>/reports/comparison/report-*.md`, Phase 8.5, or global `.specfact/reports/comparison/` if no bundle context)
- `--mode {cicd|copilot}` - Operational mode (default: auto-detect)

**Code vs Plan Drift Detection:**

The `--code-vs-plan` flag is a convenience alias that compares your intended design (manual plan) with actual implementation (code-derived plan from `import from-code`). Auto-derived plans come from code analysis, so this comparison IS "code vs plan drift" - detecting deviations between what you planned and what's actually in your code.

**Example:**

```bash
# Detect code vs plan drift (convenience alias)
specfact plan compare --code-vs-plan
# → Compares intended design (manual plan) vs actual implementation (code-derived plan)
# → Auto-derived plans come from `import from-code` (code analysis), so comparison IS "code vs plan drift"

# Explicit comparison (bundle directory paths)
specfact plan compare \
  --manual .specfact/projects/main \
  --auto .specfact/projects/my-project-auto \
  --output-format markdown \
  --out .specfact/projects/<bundle-name>/reports/comparison/deviation.md
```

**Output includes:**

- Missing features (in manual but not in auto - planned but not implemented)
- Extra features (in auto but not in manual - implemented but not planned)
- Mismatched stories
- Confidence scores
- Deviation severity

**How it differs from Spec-Kit**: Spec-Kit's `/speckit.analyze` only checks artifact consistency between markdown files; SpecFact CLI detects actual code vs plan drift by comparing manual plans (intended design) with code-derived plans (actual implementation from code analysis).

---

### `project` - Project Bundle Management

Manage project bundles with persona-based workflows for agile/scrum teams.

#### `project export`

Export persona-specific sections from project bundle to Markdown for editing.

```bash
specfact project export [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--persona PERSONA` - Persona name: `product-owner`, `developer`, or `architect` (required)
- `--output PATH` - Output file path (default: `docs/project-plans/<bundle>/<persona>.md`)
- `--output-dir PATH` - Output directory (default: `docs/project-plans/<bundle>`)
- `--stdout` - Output to stdout instead of file
- `--template TEMPLATE` - Custom template name (default: uses persona-specific template)
- `--list-personas` - List all available personas and exit
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Export Product Owner view
specfact project export --bundle my-project --persona product-owner

# Export Developer view
specfact project export --bundle my-project --persona developer

# Export Architect view
specfact project export --bundle my-project --persona architect

# Export to custom location
specfact project export --bundle my-project --persona product-owner --output docs/backlog.md

# Output to stdout (for piping/CI)
specfact project export --bundle my-project --persona product-owner --stdout
```

**What it exports:**

**Product Owner Export:**

- Definition of Ready (DoR) checklist for each story
- Prioritization data (priority, rank, business value scores)
- Dependencies (story-to-story, feature-to-feature)
- Business value descriptions and metrics
- Sprint planning data (target dates, sprints, releases)

**Developer Export:**

- Acceptance criteria for features and stories
- User stories with detailed context
- Implementation tasks with file paths
- API contracts and test scenarios
- Code mappings (source and test functions)
- Sprint context (story points, priority, dependencies)
- Definition of Done checklist

**Architect Export:**

- Technical constraints per feature
- Architectural decisions (technology choices, patterns)
- Non-functional requirements (performance, scalability, security)
- Protocols & state machines (complete definitions)
- Contracts (OpenAPI/AsyncAPI details)
- Risk assessment and mitigation strategies
- Deployment architecture

**See**: [Agile/Scrum Workflows Guide](../guides/agile-scrum-workflows.md) for detailed persona workflow documentation.

#### `project import`

Import persona edits from Markdown back into project bundle.

```bash
specfact project import [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--persona PERSONA` - Persona name: `product-owner`, `developer`, or `architect` (required)
- `--source PATH` - Source Markdown file (required)
- `--dry-run` - Validate without applying changes
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Import Product Owner edits
specfact project import --bundle my-project --persona product-owner --source docs/backlog.md

# Import Developer edits
specfact project import --bundle my-project --persona developer --source docs/developer.md

# Import Architect edits
specfact project import --bundle my-project --persona architect --source docs/architect.md

# Dry-run to validate without applying
specfact project import --bundle my-project --persona product-owner --source docs/backlog.md --dry-run
```

**What it validates:**

- **Template Structure**: Required sections present
- **DoR Completeness**: All Definition of Ready criteria met
- **Dependency Integrity**: No circular dependencies, all references exist
- **Priority Consistency**: Valid priority formats (P0-P3, MoSCoW)
- **Date Formats**: ISO 8601 date validation
- **Story Point Ranges**: Valid Fibonacci-like values

**See**: [Agile/Scrum Workflows Guide](../guides/agile-scrum-workflows.md) for detailed validation rules and examples.

#### `project merge`

Merge project bundles using three-way merge with persona-aware conflict resolution.

```bash
specfact project merge [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--base BRANCH_OR_COMMIT` - Base branch/commit (common ancestor, required)
- `--ours BRANCH_OR_COMMIT` - Our branch/commit (current branch, required)
- `--theirs BRANCH_OR_COMMIT` - Their branch/commit (incoming branch, required)
- `--persona-ours PERSONA` - Persona who made our changes (e.g., `product-owner`, required)
- `--persona-theirs PERSONA` - Persona who made their changes (e.g., `architect`, required)
- `--output PATH` - Output directory for merged bundle (default: current bundle directory)
- `--strategy STRATEGY` - Merge strategy: `auto` (persona-based), `ours`, `theirs`, `base`, `manual` (default: `auto`)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Merge with automatic persona-based resolution
specfact project merge \
  --bundle my-project \
  --base main \
  --ours po-branch \
  --theirs arch-branch \
  --persona-ours product-owner \
  --persona-theirs architect

# Merge with manual strategy
specfact project merge \
  --bundle my-project \
  --base main \
  --ours feature-1 \
  --theirs feature-2 \
  --persona-ours developer \
  --persona-theirs developer \
  --strategy manual

# Non-interactive merge (for CI/CD)
specfact project merge \
  --bundle my-project \
  --base main \
  --ours HEAD \
  --theirs origin/feature \
  --persona-ours product-owner \
  --persona-theirs architect \
  --no-interactive
```

**How it works:**

1. **Loads three versions**: Base (common ancestor), ours (current branch), and theirs (incoming branch)
2. **Detects conflicts**: Compares all three versions to find conflicting changes
3. **Resolves automatically**: Uses persona ownership rules to auto-resolve conflicts:
   - If only one persona owns the conflicting section → that persona's version wins
   - If both personas own it and they're the same → ours wins
   - If both personas own it and they're different → requires manual resolution
4. **Interactive resolution**: For unresolved conflicts, prompts you to choose:
   - `ours` - Keep our version
   - `theirs` - Keep their version
   - `base` - Keep base version
   - `manual` - Enter custom value
5. **Saves merged bundle**: Writes the resolved bundle to the output directory

**Merge Strategies:**

- **`auto`** (default): Persona-based automatic resolution
- **`ours`**: Always prefer our version for conflicts
- **`theirs`**: Always prefer their version for conflicts
- **`base`**: Always prefer base version for conflicts
- **`manual`**: Require manual resolution for all conflicts

**See**: [Conflict Resolution Workflows](../guides/agile-scrum-workflows.md#conflict-resolution) for detailed workflow examples.

#### `project resolve-conflict`

Resolve a specific conflict in a project bundle after a merge operation.

```bash
specfact project resolve-conflict [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--path CONFLICT_PATH` - Conflict path (e.g., `features.FEATURE-001.title`, required)
- `--resolution RESOLUTION` - Resolution: `ours`, `theirs`, `base`, or manual value (required)
- `--persona PERSONA` - Persona resolving the conflict (for ownership validation, optional)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Resolve conflict by keeping our version
specfact project resolve-conflict \
  --bundle my-project \
  --path features.FEATURE-001.title \
  --resolution ours

# Resolve conflict by keeping their version
specfact project resolve-conflict \
  --bundle my-project \
  --path idea.intent \
  --resolution theirs \
  --persona product-owner

# Resolve conflict with manual value
specfact project resolve-conflict \
  --bundle my-project \
  --path features.FEATURE-001.title \
  --resolution "Custom Feature Title"
```

**Conflict Path Format:**

- `idea.title` - Idea title
- `idea.intent` - Idea intent
- `business.value_proposition` - Business value proposition
- `product.themes` - Product themes (list)
- `features.FEATURE-001.title` - Feature title
- `features.FEATURE-001.stories.STORY-001.description` - Story description

**Note**: This command is a helper for resolving individual conflicts after a merge. For full merge operations, use `project merge`.

**See**: [Conflict Resolution Workflows](../guides/agile-scrum-workflows.md#conflict-resolution) for detailed workflow examples.

#### `project lock`

Lock a section for a persona to prevent concurrent edits.

```bash
specfact project lock [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--section SECTION` - Section pattern to lock (e.g., `idea`, `features.*.stories`, required)
- `--persona PERSONA` - Persona name (e.g., `product-owner`, `architect`, required)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Lock idea section for product owner
specfact project lock --bundle my-project --section idea --persona product-owner

# Lock all feature stories for product owner
specfact project lock --bundle my-project --section "features.*.stories" --persona product-owner

# Lock protocols for architect
specfact project lock --bundle my-project --section protocols --persona architect
```

**How it works:**

1. **Validates ownership**: Checks that the persona owns the section (based on manifest)
2. **Checks existing locks**: Fails if section is already locked
3. **Creates lock**: Adds lock to bundle manifest with timestamp and user info
4. **Saves bundle**: Updates bundle manifest with lock information

**Lock Enforcement**: Once locked, only the locking persona (or unlock command) can modify the section. Import operations will be blocked if attempting to edit a locked section owned by a different persona.

**See**: [Section Locking](../guides/agile-scrum-workflows.md#section-locking) for detailed workflow examples.

#### `project unlock`

Unlock a section to allow edits by any persona that owns it.

```bash
specfact project unlock [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--section SECTION` - Section pattern to unlock (e.g., `idea`, `features.*.stories`, required)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Unlock idea section
specfact project unlock --bundle my-project --section idea

# Unlock all feature stories
specfact project unlock --bundle my-project --section "features.*.stories"
```

**How it works:**

1. **Finds lock**: Searches for matching lock in bundle manifest
2. **Removes lock**: Removes lock from manifest
3. **Saves bundle**: Updates bundle manifest

**Note**: Unlock doesn't require a persona parameter - anyone can unlock a section (coordination is expected at team level).

**See**: [Section Locking](../guides/agile-scrum-workflows.md#section-locking) for detailed workflow examples.

#### `project locks`

List all current section locks in a project bundle.

```bash
specfact project locks [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# List all locks
specfact project locks --bundle my-project
```

**Output Format:**

Displays a table with:

- **Section**: Section pattern that's locked
- **Owner**: Persona who locked the section
- **Locked At**: ISO 8601 timestamp when lock was created
- **Locked By**: User@hostname who created the lock

**Use Cases:**

- Check what's locked before starting work
- Coordinate with team members about lock usage
- Identify stale locks that need cleanup

**See**: [Section Locking](../guides/agile-scrum-workflows.md#section-locking) for detailed workflow examples.

---

#### `project init-personas`

Initialize personas in project bundle manifest for persona-based workflows.

```bash
specfact project init-personas [OPTIONS]
```

**Purpose:**

Adds default persona mappings to the bundle manifest if they are missing. Useful for migrating existing bundles to use persona workflows or setting up new bundles for team collaboration.

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name. If not specified, attempts to auto-detect or prompt.
- `--persona PERSONA` - Specific persona(s) to initialize (can be repeated). If not specified, initializes all default personas.
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Default Personas:**

When no specific personas are specified, the following default personas are initialized:

- **product-owner**: Owns idea, features metadata, and stories acceptance criteria
- **architect**: Owns contracts, protocols, and technical constraints
- **developer**: Owns implementation details, file paths, and technical stories

**Examples:**

```bash
# Initialize all default personas
specfact project init-personas --bundle legacy-api

# Initialize specific personas only
specfact project init-personas --bundle legacy-api --persona product-owner --persona architect

# Non-interactive mode for CI/CD
specfact project init-personas --bundle legacy-api --no-interactive
```

**When to Use:**

- After creating a new bundle with `plan init`
- When migrating existing bundles to persona workflows
- When adding new team members with specific roles
- Before using `project export/import` persona commands

---

#### `project version check`

Check if a version bump is recommended based on bundle changes.

```bash
specfact project version check [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--repo PATH` - Path to repository (default: `.`)

**Output:**

Returns a recommendation (`major`, `minor`, `patch`, or `none`) based on:

- **major**: Breaking changes detected (API contracts modified, features removed)
- **minor**: New features added, stories added
- **patch**: Bug fixes, documentation changes, story updates
- **none**: No significant changes detected

**Examples:**

```bash
# Check version bump recommendation
specfact project version check --bundle legacy-api
```

**CI/CD Integration:**

Configure behavior via `SPECFACT_VERSION_CHECK_MODE` environment variable:

- `info`: Informational only, logs recommendations
- `warn` (default): Logs warnings but continues
- `block`: Fails CI if recommendation is not followed

---

#### `project version bump`

Apply a SemVer version bump to the project bundle.

```bash
specfact project version bump [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--type TYPE` - Bump type: `major`, `minor`, `patch` (required)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Bump minor version (e.g., 1.0.0 → 1.1.0)
specfact project version bump --bundle legacy-api --type minor

# Bump patch version (e.g., 1.1.0 → 1.1.1)
specfact project version bump --bundle legacy-api --type patch
```

**What it does:**

1. Reads current version from bundle manifest
2. Applies SemVer bump based on type
3. Records version history with timestamp
4. Updates bundle hash

---

#### `project version set`

Set an explicit version for the project bundle.

```bash
specfact project version set [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--version VERSION` - SemVer version string (e.g., `2.0.0`, `1.5.0-beta.1`)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Set explicit version
specfact project version set --bundle legacy-api --version 2.0.0

# Set pre-release version
specfact project version set --bundle legacy-api --version 1.5.0-beta.1
```

**Use Cases:**

- Initial version setup for new bundles
- Aligning with external version requirements
- Setting pre-release or build metadata versions

---

#### `project link-backlog`

Link a project bundle to a backlog provider so project health/devops commands can resolve adapter and project context automatically.

```bash
specfact project link-backlog [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (or use active bundle)
- `--project-name NAME` - Alias for `--bundle`
- `--adapter ADAPTER` - Backlog adapter id (for example: `github`, `ado`, `jira`) (required)
- `--project-id PROJECT_ID` - Provider project identifier (required)
- `--template TEMPLATE` - Optional mapping template override
- `--repo PATH` - Path to repository (default: `.`)
- `--no-interactive` - Non-interactive mode

**Example:**

```bash
specfact project link-backlog --bundle cross-sync-test --adapter github --project-id nold-ai/specfact-cli --template github_projects
```

---

#### `project health-check`

Run project-level health checks with backlog graph metrics and cross-checks.

```bash
specfact project health-check [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (or use active bundle)
- `--project-name NAME` - Alias for `--bundle`
- `--verbose` - Show linked adapter/project/template diagnostics
- `--repo PATH` - Path to repository (default: `.`)
- `--no-interactive` - Non-interactive mode

**What it checks:**

- Backlog graph health (typed items, dependencies, orphans, cycles)
- Spec-code alignment via `enforce sdd`
- Release readiness via backlog dependency/readiness verification

---

#### `project devops-flow`

Run a stage/action workflow from one project command surface.

```bash
specfact project devops-flow --stage <stage> --action <action> [OPTIONS]
```

**Supported stage/action pairs:**

- `plan/generate-roadmap`
- `develop/sync`
- `review/validate-pr`
- `release/verify`
- `monitor/health-check`

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (or use active bundle)
- `--project-name NAME` - Alias for `--bundle`
- `--stage STAGE` - Stage to execute (required)
- `--action ACTION` - Stage action (required)
- `--verbose` - Show additional diagnostics
- `--repo PATH` - Path to repository (default: `.`)
- `--no-interactive` - Non-interactive mode

---

#### `project snapshot`

Save the current linked backlog graph as baseline snapshot.

```bash
specfact project snapshot [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (or use active bundle)
- `--project-name NAME` - Alias for `--bundle`
- `--output PATH` - Baseline graph output path (default: `.specfact/backlog-baseline.json`)
- `--repo PATH` - Path to repository (default: `.`)
- `--no-interactive` - Non-interactive mode

---

#### `project regenerate`

Re-derive merged plan/backlog view and report mismatches.

```bash
specfact project regenerate [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (or use active bundle)
- `--project-name NAME` - Alias for `--bundle`
- `--strict` - Exit non-zero when mismatches are found
- `--verbose` - Print detailed mismatch entries (default is summary only)
- `--repo PATH` - Path to repository (default: `.`)
- `--no-interactive` - Non-interactive mode

---

#### `project export-roadmap`

Export roadmap milestones from backlog critical path.

```bash
specfact project export-roadmap [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (or use active bundle)
- `--project-name NAME` - Alias for `--bundle`
- `--output PATH` - Optional roadmap markdown output path
- `--repo PATH` - Path to repository (default: `.`)
- `--no-interactive` - Non-interactive mode

---

### `contract` - OpenAPI Contract Management

Manage OpenAPI contracts for project bundles, including initialization, validation, mock server generation, and test generation.

#### `contract init`

Initialize OpenAPI contract for a feature.

```bash
specfact contract init [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--feature FEATURE_KEY` - Feature key (e.g., `FEATURE-001`, required)
- `--title TITLE` - API title (default: feature title)
- `--version VERSION` - API version (default: `1.0.0`)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Initialize contract for a feature
specfact contract init --bundle legacy-api --feature FEATURE-001

# Initialize with custom title and version
specfact contract init --bundle legacy-api --feature FEATURE-001 --title "Authentication API" --version 1.0.0
```

**What it does:**

1. Creates OpenAPI 3.0.3 contract stub in `contracts/FEATURE-001.openapi.yaml`
2. Links contract to feature in bundle manifest
3. Updates contract index in manifest for fast lookup

**Note**: Defaults to OpenAPI 3.0.3 for Specmatic compatibility. Validation accepts both 3.0.x and 3.1.x for forward compatibility.

#### `contract validate`

Validate OpenAPI contract schema.

```bash
specfact contract validate [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--feature FEATURE_KEY` - Feature key (optional, validates all contracts if not specified)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Validate specific feature contract
specfact contract validate --bundle legacy-api --feature FEATURE-001

# Validate all contracts in bundle
specfact contract validate --bundle legacy-api
```

**What it does:**

1. Loads OpenAPI contract(s) from bundle
2. Validates schema structure (supports both 3.0.x and 3.1.x)
3. Reports validation results with endpoint counts

**Note**: For comprehensive validation including Specmatic, use `specfact spec validate`.

#### `contract verify`

Verify OpenAPI contract - validate, generate examples, and test mock server. This is a convenience command that combines multiple steps into one.

```bash
specfact contract verify [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--feature FEATURE_KEY` - Feature key (optional, verifies all contracts if not specified)
- `--port PORT` - Port number for mock server (default: `9000`)
- `--skip-mock` - Skip mock server startup (only validate contract)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Verify a specific contract (validates, generates examples, starts mock server)
specfact contract verify --bundle legacy-api --feature FEATURE-001

# Verify all contracts in a bundle
specfact contract verify --bundle legacy-api

# Verify without starting mock server (CI/CD)
specfact contract verify --bundle legacy-api --feature FEATURE-001 --skip-mock --no-interactive
```

**What it does:**

1. **Step 1: Validates contracts** - Checks OpenAPI schema structure
2. **Step 2: Generates examples** - Creates example JSON files from contract schema
3. **Step 3: Starts mock server** - Launches Specmatic mock server (unless `--skip-mock`)
4. **Step 4: Tests connectivity** - Verifies mock server is responding

**Output:**

```text
Step 1: Validating contracts...
✓ FEATURE-001: Valid (13 endpoints)

Step 2: Generating examples...
✓ FEATURE-001: Examples generated

Step 3: Starting mock server for FEATURE-001...
✓ Mock server started at http://localhost:9000

Step 4: Testing connectivity...
✓ Health check passed: UP

✓ Contract verification complete!

Summary:
  • Contracts validated: 1
  • Examples generated: 1
  • Mock server: http://localhost:9000
```

**When to use:**

- **Quick verification** - One command to verify everything works
- **Development** - Start mock server and verify contract is correct
- **CI/CD** - Use `--skip-mock --no-interactive` for fast validation
- **Multiple contracts** - Verify all contracts in a bundle at once

**Note**: This is the recommended command for most use cases. It combines validation, example generation, and mock server testing into a single, simple workflow.

#### `contract serve`

Start mock server for OpenAPI contract.

```bash
specfact contract serve [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--feature FEATURE_KEY` - Feature key (optional, prompts for selection if multiple contracts)
- `--port PORT` - Port number for mock server (default: `9000`)
- `--strict/--examples` - Use strict validation mode or examples mode (default: `strict`)
- `--no-interactive` - Non-interactive mode (uses first contract if multiple available)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Start mock server for specific feature contract
specfact contract serve --bundle legacy-api --feature FEATURE-001

# Start mock server on custom port with examples mode
specfact contract serve --bundle legacy-api --feature FEATURE-001 --port 8080 --examples
```

**What it does:**

1. Loads OpenAPI contract from bundle
2. Launches Specmatic mock server
3. Serves API endpoints based on contract
4. Validates requests against spec
5. Returns example responses

**Requirements**: Specmatic must be installed (`npm install -g @specmatic/specmatic`)

> **Press Ctrl+C to stop the server**

#### `contract test`

Generate contract tests from OpenAPI contract.

```bash
specfact contract test [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--feature FEATURE_KEY` - Feature key (optional, generates tests for all contracts if not specified)
- `--output PATH` - Output directory for generated tests (default: bundle-specific `.specfact/projects/<bundle-name>/tests/contracts/`)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Generate tests for specific feature contract
specfact contract test --bundle legacy-api --feature FEATURE-001

# Generate tests for all contracts in bundle
specfact contract test --bundle legacy-api

# Generate tests to custom output directory
specfact contract test --bundle legacy-api --output tests/contracts/
```

**What it does:**

1. Loads OpenAPI contract(s) from bundle
2. Generates Specmatic test suite(s) using `specmatic generate-tests`
3. Saves tests to bundle-specific or custom output directory
4. Creates feature-specific test directories for organization

**Requirements**: Specmatic must be installed (`npm install -g @specmatic/specmatic`)

**Output Structure:**

```text
.specfact/projects/<bundle-name>/tests/contracts/
├── feature-001/
│   └── [Specmatic-generated test files]
├── feature-002/
│   └── [Specmatic-generated test files]
└── ...
```

#### `contract coverage`

Calculate contract coverage for a project bundle.

```bash
specfact contract coverage [OPTIONS]
```

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name (required, or auto-detect)
- `--no-interactive` - Non-interactive mode (for CI/CD automation)
- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# Get coverage report for bundle
specfact contract coverage --bundle legacy-api
```

**What it does:**

1. Loads all features from bundle
2. Checks which features have contracts
3. Calculates coverage percentage (features with contracts / total features)
4. Counts total API endpoints across all contracts
5. Displays coverage table with status indicators

**Output:**

- Coverage table showing feature, contract file, endpoint count, and status
- Coverage summary with percentage and total endpoints
- Warning if coverage is below 100%

**See**: [Specmatic Integration Guide](../guides/specmatic-integration.md) for detailed contract testing workflow.

---

### `enforce` - Configure Quality Gates

Set contract enforcement policies.

#### `enforce sdd`

Validate SDD manifest against plan bundle and contracts:

```bash
specfact enforce sdd [OPTIONS]
```

**Options:**

- Bundle name is provided as a positional argument (e.g., `plan harden my-project`)
- `--sdd PATH` - SDD manifest path (default: bundle-specific `.specfact/projects/<bundle-name>/sdd.<format>`, Phase 8.5)
- `--output-format {markdown,json,yaml}` - Output format (default: markdown)
- `--out PATH` - Output report path (optional)

**What it validates:**

1. **Hash Match**: Verifies SDD manifest is linked to the correct plan bundle
2. **Coverage Thresholds**: Validates contract density metrics:
   - Contracts per story (must meet threshold)
   - Invariants per feature (must meet threshold)
   - Architecture facets (must meet threshold)
3. **SDD Structure**: Validates SDD manifest schema and completeness

**Contract Density Metrics:**

The command calculates and validates:

- **Contracts per story**: Total contracts divided by total stories
- **Invariants per feature**: Total invariants divided by total features
- **Architecture facets**: Number of architecture-related constraints

**Example:**

```bash
# Validate SDD against active plan
specfact enforce sdd

# Validate with specific bundle and SDD (bundle name as positional argument)
specfact enforce sdd main  # Uses .specfact/projects/main/sdd.yaml (Phase 8.5)

# Generate JSON report
specfact enforce sdd --output-format json --out validation-report.json
```

**Output:**

- Validation status (pass/fail)
- Contract density metrics with threshold comparisons
- Deviations report with severity levels (HIGH/MEDIUM/LOW)
- Fix hints for each deviation

**Deviations:**

The command reports deviations when:

- Hash mismatch (SDD linked to different plan)
- Contracts per story below threshold
- Invariants per feature below threshold
- Architecture facets below threshold

**Integration:**

- Automatically called by `plan review` when SDD is present
- Required for `plan promote` to "review" or higher stages
- Part of standard SDD enforcement workflow

#### `enforce stage`

Configure enforcement stage:

```bash
specfact enforce stage [OPTIONS]
```

**Options:**

- `--preset TEXT` - Enforcement preset (minimal, balanced, strict) (required)
- `--config PATH` - Enforcement config file

**Presets:**

| Preset | HIGH Severity | MEDIUM Severity | LOW Severity |
|--------|---------------|-----------------|--------------|
| **minimal** | Log only | Log only | Log only |
| **balanced** | Block | Warn | Log only |
| **strict** | Block | Block | Warn |

**Example:**

```bash
# Start with minimal
specfact enforce stage --preset minimal

# Move to balanced after stabilization
specfact enforce stage --preset balanced

# Strict for production
specfact enforce stage --preset strict
```

---

### `drift` - Detect Drift Between Code and Specifications

Detect misalignment between code and specifications.

#### `drift detect`

Detect drift between code and specifications.

```bash
specfact drift detect [BUNDLE] [OPTIONS]
```

**Arguments:**

- `BUNDLE` - Project bundle name (e.g., `legacy-api`). Default: active plan from `specfact plan select`

**Options:**

- `--repo PATH` - Path to repository. Default: current directory (`.`)
- `--format {table,json,yaml}` - Output format. Default: `table`
- `--out PATH` - Output file path (for JSON/YAML format). Default: stdout

**What it detects:**

- **Added code** - Files with no spec (untracked implementation files)
- **Removed code** - Deleted files but spec still exists
- **Modified code** - Files with hash changed (implementation modified)
- **Orphaned specs** - Specifications with no source tracking (no linked code)
- **Test coverage gaps** - Stories missing test functions
- **Contract violations** - Implementation doesn't match contract (requires Specmatic)

**Examples:**

```bash
# Detect drift for active plan
specfact drift detect

# Detect drift for specific bundle
specfact drift detect legacy-api --repo .

# Output to JSON file
specfact drift detect my-bundle --format json --out drift-report.json

# Output to YAML file
specfact drift detect my-bundle --format yaml --out drift-report.yaml
```

**Output Formats:**

- **Table** (default) - Rich formatted table with color-coded sections
- **JSON** - Machine-readable JSON format for CI/CD integration
- **YAML** - Human-readable YAML format

**Integration:**

The drift detection command integrates with:

- Source tracking (hash-based change detection)
- Project bundles (feature and story tracking)
- Specmatic (contract validation, if available)

**See also:**

- `plan compare` - Compare plans to detect code vs plan drift
- `sync intelligent` - Continuous sync with drift detection

---

### `repro` - Reproducibility Validation

Run full validation suite for reproducibility.

```bash
specfact repro [OPTIONS]
```

**Options:**

- `--repo PATH` - Path to repository (default: current directory)
- `--verbose` - Show detailed output
- `--fix` - Apply auto-fixes where available (Semgrep auto-fixes)
- `--fail-fast` - Stop on first failure
- `--out PATH` - Output report path (default: bundle-specific `.specfact/projects/<bundle-name>/reports/enforcement/report-<timestamp>.yaml`, Phase 8.5, or global `.specfact/reports/enforcement/` if no bundle context)
- `--sidecar` - Run sidecar validation for unannotated code (no-edit path)
- `--sidecar-bundle NAME` - Bundle name for sidecar validation (required if --sidecar is used)

**Advanced Options** (hidden by default, use `--help-advanced` or `-ha` to view):

- `--budget INT` - Time budget in seconds (default: 120)

**Subcommands:**

- `repro setup` - Set up CrossHair configuration for contract exploration
  - Automatically generates `[tool.crosshair]` configuration in `pyproject.toml`
  - Detects source directories and environment manager
  - Checks for crosshair-tool availability
  - Provides installation guidance if needed

**Example:**

```bash
# First-time setup: Configure CrossHair for contract exploration
specfact repro setup

# Standard validation (current directory)
specfact repro --verbose --budget 120

# Validate external repository
specfact repro --repo /path/to/external/repo --verbose

# Apply auto-fixes for violations
specfact repro --fix --budget 120

# Stop on first failure
specfact repro --fail-fast

# Run repro with sidecar validation for unannotated code
specfact repro --sidecar --sidecar-bundle legacy-api --repo /path/to/repo
```

**What it runs:**

1. **Lint checks** - ruff, semgrep async rules
2. **Type checking** - mypy/basedpyright
3. **Contract exploration** - CrossHair
4. **Property tests** - Hypothesis
5. **Smoke tests** - Event loop lag, orphaned tasks
6. **Plan validation** - Schema compliance
7. **Sidecar validation** - Optional, for unannotated code (when `--sidecar` flag is used)

**External Repository Support:**

The `repro` command automatically detects the target repository's environment manager and adapts commands accordingly:

- **Environment Detection**: Automatically detects hatch, poetry, uv, or pip-based projects
- **Tool Availability**: All tools are optional - missing tools are skipped with clear messages
- **Source Detection**: Automatically detects source directories (`src/`, `lib/`, or package name from `pyproject.toml`)
- **Cross-Repository**: Works on external repositories without requiring SpecFact CLI adoption

**Supported Environment Managers:**

SpecFact CLI automatically detects and works with the following project management tools:

- **hatch** - Detected from `[tool.hatch]` in `pyproject.toml`
  - Commands prefixed with: `hatch run`
  - Example: `hatch run pytest tests/`
  
- **poetry** - Detected from `[tool.poetry]` in `pyproject.toml` or `poetry.lock`
  - Commands prefixed with: `poetry run`
  - Example: `poetry run pytest tests/`
  
- **uv** - Detected from `[tool.uv]` in `pyproject.toml`, `uv.lock`, or `uv.toml`
  - Commands prefixed with: `uv run`
  - Example: `uv run pytest tests/`
  
- **pip** - Detected from `requirements.txt` or `setup.py` (uses direct tool invocation)
  - Commands use: Direct tool invocation (no prefix)
  - Example: `pytest tests/`

**Detection Priority**:

1. Checks `pyproject.toml` for tool sections (`[tool.hatch]`, `[tool.poetry]`, `[tool.uv]`)
2. Checks for lock files (`poetry.lock`, `uv.lock`, `uv.toml`)
3. Falls back to `requirements.txt` or `setup.py` for pip-based projects

**Source Directory Detection**:

- Automatically detects: `src/`, `lib/`, or package name from `pyproject.toml`
- Works with any project structure without manual configuration

**Tool Requirements:**

Tools are checked for availability and skipped if not found:

- **ruff** - Optional, for linting
- **semgrep** - Optional, only runs if `tools/semgrep/async.yml` config exists
- **basedpyright** - Optional, for type checking
- **crosshair** - Optional, for contract exploration (requires `[tool.crosshair]` config in `pyproject.toml` - use `specfact repro setup` to generate)
- **sidecar** - Optional, for validating unannotated code without modifying source (use `--sidecar --sidecar-bundle <name>`)
- **pytest** - Optional, only runs if `tests/contracts/` or `tests/smoke/` directories exist

**Auto-fixes:**

When using `--fix`, Semgrep will automatically apply fixes for violations that have `fix:` fields in the rules. For example, `blocking-sleep-in-async` rule will automatically replace `time.sleep(...)` with `asyncio.sleep(...)` in async functions.

**Exit codes:**

- `0` - All checks passed
- `1` - Validation failed
- `2` - Budget exceeded

**Report Format:**

Reports are written as YAML files to `.specfact/projects/<bundle-name>/reports/enforcement/report-<timestamp>.yaml` (bundle-specific, Phase 8.5). Each report includes:

**Summary Statistics:**

- `total_duration` - Total time taken (seconds)
- `total_checks` - Number of checks executed
- `passed_checks`, `failed_checks`, `timeout_checks`, `skipped_checks` - Status counts
- `budget_exceeded` - Whether time budget was exceeded

**Check Details:**

- `checks` - List of check results with:
  - `name` - Human-readable check name
  - `tool` - Tool used (ruff, semgrep, basedpyright, crosshair, pytest)
  - `status` - Check status (passed, failed, timeout, skipped)
  - `duration` - Time taken (seconds)
  - `exit_code` - Tool exit code
  - `timeout` - Whether check timed out
  - `output_length` - Length of output (truncated in report)
  - `error_length` - Length of error output (truncated in report)

**Metadata (Context):**

- `timestamp` - When the report was generated (ISO format)
- `repo_path` - Repository path (absolute)
- `budget` - Time budget used (seconds)
- `active_plan_path` - Active plan bundle path (relative to repo, if exists)
- `enforcement_config_path` - Enforcement config path (relative to repo, if exists)
- `enforcement_preset` - Enforcement preset used (minimal, balanced, strict, if config exists)
- `fix_enabled` - Whether `--fix` flag was used (true/false)
- `fail_fast` - Whether `--fail-fast` flag was used (true/false)

**Example Report:**

```yaml
total_duration: 89.09
total_checks: 4
passed_checks: 1
failed_checks: 2
timeout_checks: 1
skipped_checks: 0
budget_exceeded: false
checks:
  - name: Linting (ruff)
    tool: ruff
    status: failed
    duration: 0.03
    exit_code: 1
    timeout: false
    output_length: 39324
    error_length: 0
  - name: Async patterns (semgrep)
    tool: semgrep
    status: passed
    duration: 0.21
    exit_code: 0
    timeout: false
    output_length: 0
    error_length: 164
metadata:
  timestamp: '2025-11-06T00:43:42.062620'
  repo_path: /home/user/my-project
  budget: 120
  active_plan_path: .specfact/projects/main/
  enforcement_config_path: .specfact/gates/config/enforcement.yaml
  enforcement_preset: balanced
  fix_enabled: false
  fail_fast: false
```

---

### `generate` - Generate Artifacts

Generate contract stubs and other artifacts from SDD manifests.

#### `generate contracts`

Generate contract stubs from SDD manifest:

```bash
specfact generate contracts [OPTIONS]
```

**Options:**

- Bundle name is provided as a positional argument (e.g., `plan harden my-project`)
- `--sdd PATH` - SDD manifest path (default: bundle-specific `.specfact/projects/<bundle-name>/sdd.<format>`, Phase 8.5)
- `--out PATH` - Output directory (default: `.specfact/contracts/`)
- `--output-format {yaml,json}` - SDD manifest format (default: auto-detect)

**What it generates:**

1. **Contract stubs** with `icontract` decorators:
   - Preconditions (`@require`)
   - Postconditions (`@ensure`)
   - Invariants (`@invariant`)
2. **Type checking** with `beartype` decorators
3. **CrossHair harnesses** for property-based testing
4. **One file per feature/story** in `.specfact/contracts/`

**Validation:**

- **Hash match**: Verifies SDD manifest is linked to the correct plan bundle
- **Plan bundle hash**: Must match SDD manifest's `plan_bundle_hash`
- **Error handling**: Reports hash mismatch with clear error message

**Example:**

```bash
# Generate contracts from active plan and SDD
specfact generate contracts

# Generate with specific bundle and SDD (bundle name as positional argument)
specfact generate contracts --bundle main  # Uses .specfact/projects/main/sdd.yaml (Phase 8.5)

# Custom output directory
specfact generate contracts --out src/contracts/
```

**Workflow:**

1. **Create SDD**: `specfact plan harden` (creates SDD manifest and saves plan with hash)
2. **Generate contracts**: `specfact generate contracts` (validates hash match, generates stubs)
3. **Implement contracts**: Add contract logic to generated stubs
4. **Enforce**: `specfact enforce sdd` (validates contract density)

**Important Notes:**

- **Hash validation**: Command validates that SDD manifest's `plan_bundle_hash` matches the plan bundle's current hash
- **Plan bundle must be saved**: Ensure `plan harden` has saved the plan bundle with updated hash before running `generate contracts`
- **Contract density**: After generation, run `specfact enforce sdd` to validate contract density metrics

**Output Structure:**

```shell
.specfact/contracts/
├── feature_001_contracts.py
├── feature_002_contracts.py
└── ...
```

Each file includes:

- Contract decorators (`@icontract`, `@beartype`)
- CrossHair harnesses for property testing
- Backlink metadata to SDD IDs
- Plan bundle story/feature references

---

#### `generate contracts-prompt`

Generate AI IDE prompts for adding contracts to existing code files:

```bash
specfact generate contracts-prompt [FILE] [OPTIONS]
```

**Purpose:**

Creates structured prompt files that you can use with your AI IDE (Cursor, CoPilot, etc.) to add beartype, icontract, or CrossHair contracts to existing Python code. The CLI generates the prompt, your AI IDE's LLM applies the contracts.

**Options:**

- `FILE` - Path to file to enhance (optional if `--bundle` provided)
- `--bundle BUNDLE_NAME` - Project bundle name. If provided, selects files from bundle. Default: active plan from `specfact plan select`
- `--apply CONTRACTS` - **Required**. Contracts to apply: `all-contracts`, `beartype`, `icontract`, `crosshair`, or comma-separated list (e.g., `beartype,icontract`)
- `--no-interactive` - Non-interactive mode (for CI/CD automation). Disables interactive prompts.

**Advanced Options** (hidden by default, use `--help-advanced` or `-ha` to view):

- `--output PATH` - Output file path (currently unused, prompt saved to `.specfact/prompts/`)

**Contract Types:**

- `all-contracts` - Apply all available contract types (beartype, icontract, crosshair)
- `beartype` - Type checking decorators (`@beartype`)
- `icontract` - Pre/post condition decorators (`@require`, `@ensure`, `@invariant`)
- `crosshair` - Property-based test functions

**Examples:**

```bash
# Apply all contract types to a specific file
specfact generate contracts-prompt src/auth/login.py --apply all-contracts

# Apply specific contract types
specfact generate contracts-prompt src/auth/login.py --apply beartype,icontract

# Apply to all files in a bundle (interactive selection)
specfact generate contracts-prompt --bundle legacy-api --apply all-contracts

# Apply to all files in a bundle (non-interactive)
specfact generate contracts-prompt --bundle legacy-api --apply all-contracts --no-interactive
```

**How It Works:**

1. **CLI generates prompt**: Reads the file and creates a structured prompt
2. **Prompt saved**: Saved to `.specfact/projects/<bundle-name>/prompts/enhance-<filename>-<contracts>.md` (or `.specfact/prompts/` if no bundle)
3. **You copy prompt**: Copy the prompt to your AI IDE (Cursor, CoPilot, etc.)
4. **AI IDE enhances code**: AI IDE reads the file and provides enhanced code (does NOT modify file directly)
5. **AI IDE writes to temp file**: Enhanced code written to `enhanced_<filename>.py`
6. **Validate with CLI**: AI IDE runs `specfact generate contracts-apply enhanced_<filename>.py --original <original-file>`
7. **Iterative validation**: If validation fails, AI IDE fixes issues and re-validates (up to 3 attempts)
8. **Apply changes**: If validation succeeds, CLI applies changes automatically
9. **Verify and test**: Run `specfact analyze contracts --bundle <bundle>` and your test suite

**Prompt File Location:**

- **With bundle**: `.specfact/projects/<bundle-name>/prompts/enhance-<filename>-<contracts>.md`
- **Without bundle**: `.specfact/prompts/enhance-<filename>-<contracts>.md`

**Why This Approach:**

- Uses your existing AI IDE infrastructure (no separate LLM API setup)
- No additional API costs (leverages IDE's native LLM)
- You maintain control (review before committing)
- Works with any AI IDE (Cursor, CoPilot, Claude, etc.)
- Iterative validation ensures code quality before applying changes

**Complete Workflow:**

```bash
# 1. Generate prompt
specfact generate contracts-prompt src/auth/login.py --apply all-contracts

# 2. Open prompt file
cat .specfact/projects/my-bundle/prompts/enhance-login-beartype-icontract-crosshair.md

# 3. Copy prompt to your AI IDE (Cursor, CoPilot, etc.)

# 4. AI IDE reads the file and provides enhanced code (does NOT modify file directly)

# 5. AI IDE writes enhanced code to temporary file: enhanced_login.py

# 6. AI IDE runs validation
specfact generate contracts-apply enhanced_login.py --original src/auth/login.py

# 7. If validation fails, AI IDE fixes issues and re-validates (up to 3 attempts)

# 8. If validation succeeds, CLI applies changes automatically

# 9. Verify contract coverage
specfact analyze contracts --bundle my-bundle

# 10. Run your test suite
pytest

# 11. Commit the enhanced code
git add src/auth/login.py && git commit -m "feat: add contracts to login module"
```

**Validation Steps (performed by `contracts-apply`):**

The `contracts-apply` command performs rigorous validation before applying changes:

1. **File size check**: Enhanced file must not be smaller than original
2. **Python syntax validation**: Uses `python -m py_compile`
3. **AST structure comparison**: Ensures no functions or classes are accidentally removed
4. **Contract imports verification**: Checks for required imports (`beartype`, `icontract`)
5. **Test execution**: Runs `specfact repro` or `pytest` to ensure code functions correctly
6. **Diff preview**: Displays changes before applying

Only if all validation steps pass are changes applied to the original file.

**Error Messages:**

If `--apply` is missing or invalid, the CLI shows helpful error messages with:

- Available contract types and descriptions
- Usage examples
- Link to full documentation

---

#### `generate fix-prompt`

Generate AI IDE prompt for fixing a specific gap identified by analysis:

```bash
specfact generate fix-prompt [GAP_ID] [OPTIONS]
```

**Purpose:**

Creates a structured prompt file for your AI IDE (Cursor, Copilot, etc.) to fix identified gaps in your codebase. This is the **recommended workflow for v0.17+** and replaces direct code generation.

**Arguments:**

- `GAP_ID` - Gap ID to fix (e.g., `GAP-001`). If not provided, lists available gaps.

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name. Default: active plan from `specfact plan select`
- `--output PATH`, `-o PATH` - Output file path. Default: `.specfact/prompts/fix-<gap-id>.md`
- `--top N` - Show top N gaps when listing. Default: 5
- `--no-interactive` - Non-interactive mode (for CI/CD automation)

**Workflow:**

1. Run analysis to identify gaps (via `import from-code` + `repro`)
2. Run `specfact generate fix-prompt` to list available gaps
3. Run `specfact generate fix-prompt GAP-001` to generate fix prompt
4. Copy the prompt to your AI IDE (Cursor, Copilot, Claude, etc.)
5. AI IDE provides the fix
6. Validate with `specfact enforce sdd --bundle <bundle>`

**Examples:**

```bash
# List available gaps
specfact generate fix-prompt

# Generate fix prompt for specific gap
specfact generate fix-prompt GAP-001

# List gaps for specific bundle
specfact generate fix-prompt --bundle legacy-api

# Save to specific file
specfact generate fix-prompt GAP-001 --output fix.md

# Show more gaps in listing
specfact generate fix-prompt --top 10
```

**Gap Report Location:**

Gap reports are stored at `.specfact/projects/<bundle-name>/reports/gaps.json`. If no gap report exists, the command provides guidance on how to generate one.

**Why This Approach:**

- **AI IDE native**: Uses your existing AI infrastructure (no separate LLM API setup)
- **No additional costs**: Leverages IDE's native LLM
- **You maintain control**: Review fixes before committing
- **Works with any AI IDE**: Cursor, Copilot, Claude, Windsurf, etc.

---

#### `generate test-prompt`

Generate AI IDE prompt for creating tests for a file:

```bash
specfact generate test-prompt [FILE] [OPTIONS]
```

**Purpose:**

Creates a structured prompt file for your AI IDE to generate comprehensive tests for your code. This is the **recommended workflow for v0.17+**.

**Arguments:**

- `FILE` - File to generate tests for. If not provided with `--bundle`, shows files without tests.

**Options:**

- `--bundle BUNDLE_NAME` - Project bundle name. Default: active plan from `specfact plan select`
- `--output PATH`, `-o PATH` - Output file path. Default: `.specfact/prompts/test-<filename>.md`
- `--type TYPE` - Test type: `unit`, `integration`, or `both`. Default: `unit`
- `--no-interactive` - Non-interactive mode (for CI/CD automation)

**Workflow:**

1. Run `specfact generate test-prompt src/module.py` to get a test prompt
2. Copy the prompt to your AI IDE
3. AI IDE generates tests
4. Save tests to appropriate location (e.g., `tests/unit/test_module.py`)
5. Run tests with `pytest`

**Examples:**

```bash
# List files that may need tests
specfact generate test-prompt --bundle legacy-api

# Generate unit test prompt for specific file
specfact generate test-prompt src/auth/login.py

# Generate integration test prompt
specfact generate test-prompt src/api.py --type integration

# Generate both unit and integration test prompts
specfact generate test-prompt src/core/engine.py --type both

# Save to specific file
specfact generate test-prompt src/utils.py --output tests-prompt.md
```

**Test Coverage Analysis:**

When run without a file argument, the command analyzes the repository for Python files without corresponding test files and displays them in a table.

**Generated Prompt Content:**

The generated prompt includes:

- File path and content
- Test type requirements (unit/integration/both)
- Testing framework guidance (pytest, fixtures, parametrize)
- Coverage requirements based on test type
- AAA pattern (Arrange-Act-Assert) guidelines

---

#### `generate tasks` - Removed

> **⚠️ REMOVED in v0.22.0**: The `specfact generate tasks` command has been removed. Per SPECFACT_0x_TO_1x_BRIDGE_PLAN.md, SpecFact CLI does not create plan → feature → task (that's the job for spec-kit, openspec, etc.). We complement those SDD tools to enforce tests and quality.

**Previous functionality (removed):**

Generate task breakdown from project bundle and SDD manifest:

```bash
specfact generate tasks [BUNDLE] [OPTIONS]
```

**Purpose:**

Creates a dependency-ordered task list organized by development phase, linking tasks to user stories with acceptance criteria, file paths, dependencies, and parallelization markers.

**Arguments:**

- `BUNDLE` - Project bundle name (e.g., `legacy-api`). Default: active plan from `specfact plan select`

**Options:**

- `--sdd PATH` - Path to SDD manifest. Default: auto-discover from bundle name
- `--output-format FORMAT` - Output format: `yaml`, `json`, `markdown`. Default: `yaml`
- `--out PATH` - Output file path. Default: `.specfact/projects/<bundle-name>/tasks.yaml`
- `--no-interactive` - Non-interactive mode (for CI/CD automation)

**Task Phases:**

Tasks are organized into four phases:

1. **Setup**: Project structure, dependencies, configuration
2. **Foundational**: Core models, base classes, contracts
3. **User Stories**: Feature implementation tasks (linked to stories)
4. **Polish**: Tests, documentation, optimization

**Previous Examples (command removed):**

```bash
# REMOVED in v0.22.0 - Do not use
# specfact generate tasks
# specfact generate tasks legacy-api
# specfact generate tasks auth-module --output-format json
# specfact generate tasks legacy-api --output-format markdown
# specfact generate tasks legacy-api --out custom-tasks.yaml
```

**Migration:** Use Spec-Kit, OpenSpec, or other SDD tools to create tasks. SpecFact CLI focuses on enforcing tests and quality gates for existing code.

**Output Structure (YAML):**

```yaml
version: "1.0"
bundle: legacy-api
phases:
  - name: Setup
    tasks:
      - id: TASK-001
        title: Initialize project structure
        story_ref: null
        dependencies: []
        parallel: false
        files: [pyproject.toml, src/__init__.py]
  - name: User Stories
    tasks:
      - id: TASK-010
        title: Implement user authentication
        story_ref: STORY-001
        acceptance_criteria:
          - Users can log in with email/password
        dependencies: [TASK-001, TASK-005]
        parallel: true
        files: [src/auth/login.py]
```

**Note:** An SDD manifest (from `plan harden`) is recommended but not required. Without an SDD, tasks are generated based on plan bundle features and stories only.

---

### `sync` - Synchronize Changes

Bidirectional synchronization for consistent change management.

#### `sync bridge`

Sync changes between external tool artifacts and SpecFact using the bridge architecture. Supports both code/spec adapters (Spec-Kit, OpenSpec) and backlog adapters (GitHub Issues, ADO, Linear, Jira).

```bash
specfact sync bridge [OPTIONS]
```

**Adapter Types:**

- **Code/Spec adapters** (`speckit`, `openspec`, `generic-markdown`): Bidirectional sync of specifications and plans
- **Backlog adapters** (`github`, `ado`, `linear`, `jira`) 🆕: Bidirectional sync of change proposals with backlog items (import issues as proposals, export proposals as issues)

**Options:**

- `--repo PATH` - Path to repository (default: `.`)
- `--adapter ADAPTER` - Adapter type: `speckit`, `generic-markdown`, `openspec`, `github`, `ado`, `linear`, `jira`, `notion` (default: auto-detect)
- `--bundle BUNDLE_NAME` - Project bundle name for SpecFact → tool conversion (default: auto-detect)
- `--mode MODE` - Sync mode: `read-only` (OpenSpec → SpecFact), `export-only` (SpecFact → DevOps), `bidirectional` (tool ↔ SpecFact). Default: bidirectional if `--bidirectional`, else unidirectional
- `--external-base-path PATH` - Base path for external tool repository (for cross-repo integrations, e.g., OpenSpec in different repo)
- `--bidirectional` - Enable bidirectional sync (default: one-way import)
  - **For backlog adapters**: Enables import (GitHub Issues → change proposals) AND export (change proposals → GitHub Issues)
- `--overwrite` - Overwrite existing tool artifacts (delete all existing before sync)
- `--watch` - Watch mode for continuous sync (monitors file changes in real-time)
- `--interval INT` - Watch interval in seconds (default: 5, minimum: 1)
- `--ensure-compliance` - Validate and auto-enrich plan bundle for tool compliance before sync

**DevOps Backlog Integration** 🆕 **NEW FEATURE**:

When using backlog adapters (GitHub, ADO, Linear, Jira), the command provides bidirectional synchronization:

- **Export**: OpenSpec change proposals → GitHub Issues (or other backlog tools)
- **Import**: GitHub Issues → OpenSpec change proposals
- **Status Sync**: Keep OpenSpec change proposal status in sync with backlog item status
- **Progress Tracking**: Automatically detect code changes and add progress comments to issues
- **Validation Reporting**: Report validation results to backlog items

**Beyond export/update capabilities:**

- **Selective backlog import into bundles**: `--mode bidirectional` with `--backlog-ids` or `--backlog-ids-file`
- **Status sync**: Align proposal status with backlog state for linked items
- **Progress notes**: Add code progress comments via `--track-code-changes` or `--add-progress-comment`
- **Cross-adapter bundle export**: Use `--bundle` to export stored backlog content 1:1 across adapters

**🚀 Cross-Adapter Sync: Lossless Round-Trip Migration** (Advanced Feature):

One of SpecFact's most powerful capabilities for DevOps teams. Enables **lossless round-trip synchronization** between different backlog adapters (GitHub ↔ Azure DevOps ↔ others):

- **Tool Migration**: Migrate between backlog tools without losing content or metadata
- **Multi-Tool Workflows**: Sync proposals across different tools used by different teams
- **Content Fidelity**: Preserve exact formatting, sections, and metadata across adapter boundaries
- **Day-to-Day Developer Experience**: Keep backlogs in sync with feature branches, code changes, and validations

**How it works**: When importing from any backlog adapter, the original raw content (title, body) is stored in the project bundle's `source_tracking` metadata. Exporting from stored bundles preserves the original content exactly as it was imported, enabling 100% fidelity round-trips.

**Example: GitHub → ADO Migration**

```bash
# Step 1: Import GitHub issue into bundle (stores lossless content)
# Output shows: "✓ Imported GitHub issue #123 as change proposal: add-feature-x"
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner your-org --repo-name your-repo \
  --bundle main \
  --backlog-ids 123

# Step 2: Find change_id (if you missed it in output)
# Option A: Check bundle directory
ls .specfact/projects/main/change_tracking/proposals/
# Option B: Check OpenSpec changes directory
ls /path/to/openspec-repo/openspec/changes/

# Step 3: Export from bundle to ADO (uses stored lossless content)
# Use the change_id from Step 1 output (e.g., "add-feature-x")
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org --ado-project your-project \
  --bundle main \
  --change-ids add-feature-x  # Replace with actual change_id from Step 1
```

**Example: Multi-Tool Sync Workflow**

```bash
# Day 1: Create proposal, export to GitHub (public, sanitized)
# Change ID: "add-feature-x" (from openspec/changes/add-feature-x/proposal.md)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org --repo-name public-repo \
  --sanitize \
  --change-ids add-feature-x
# Output: "✓ Exported to GitHub" with issue number (e.g., #123)

# Day 2: Import GitHub issue into bundle (for internal team)
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner your-org --repo-name public-repo \
  --bundle internal \
  --backlog-ids 123
# Output: "✓ Imported GitHub issue #123 as change proposal: add-feature-x"

# Day 3: Export to ADO for internal tracking (full content, no sanitization)
# Use change_id from Day 2 output
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org --ado-project internal-project \
  --bundle internal \
  --change-ids add-feature-x  # Same change_id across all adapters
# Output: "✓ Exported to ADO" with work item ID (e.g., 456)
```

**Key Points:**

- Change IDs are shown in import/export output
- Same change_id is used across all adapters for the same proposal
- Bundle preserves lossless content for cross-adapter sync
- See [DevOps Integration Guide](../guides/devops-adapter-integration.md#cross-adapter-sync-lossless-round-trip-migration) for detailed step-by-step instructions

See [DevOps Adapter Integration Guide](../guides/devops-adapter-integration.md#cross-adapter-sync-lossless-round-trip-migration) for complete cross-adapter sync documentation.

**Quick Start:**

1. **Create change proposals** in `openspec/changes/<change-id>/proposal.md`
2. **Export to GitHub** to create issues:

   ```bash
   specfact sync bridge --adapter github --mode export-only \
     --repo-owner owner --repo-name repo \
     --repo /path/to/openspec-repo
   ```

3. **Track code changes** by adding progress comments:

  ```bash
  specfact sync bridge --adapter github --mode export-only \
    --repo-owner owner --repo-name repo \
    --track-code-changes \
    --repo /path/to/openspec-repo \
    --code-repo /path/to/source-code-repo  # If different from OpenSpec repo

  # Update existing issue with latest proposal content

  specfact sync bridge --adapter github --mode export-only \
    --repo-owner owner --repo-name repo \
    --change-ids your-change-id \
    --update-existing \
    --repo /path/to/openspec-repo
  ```

**Basic Options:**

- `--adapter github` - GitHub Issues adapter (requires GitHub API token)
- `--repo-owner OWNER` - GitHub repository owner (optional, can use bridge config)
- `--repo-name NAME` - GitHub repository name (optional, can use bridge config)
- `--github-token TOKEN` - GitHub API token (optional, uses `GITHUB_TOKEN` env var or `gh` CLI if not provided)
- `--use-gh-cli/--no-gh-cli` - Use GitHub CLI (`gh auth token`) to get token automatically (default: True). Useful in enterprise environments where PAT creation is restricted
- `--sanitize/--no-sanitize` - Sanitize proposal content for public issues (default: auto-detect based on repo setup)
  - Auto-detection: If code repo != planning repo → sanitize, if same repo → no sanitization
  - `--sanitize`: Force sanitization (removes competitive analysis, internal strategy, implementation details)
  - `--no-sanitize`: Skip sanitization (use full proposal content)
- `--target-repo OWNER/REPO` - Target repository for issue creation (format: owner/repo). Default: same as code repository
- `--interactive` - Interactive mode for AI-assisted sanitization (requires slash command)
- `--change-ids ID1,ID2` - Comma-separated list of change proposal IDs to export (default: all active proposals)
- `--backlog-ids ID1,ID2` - Comma-separated list of backlog item IDs/URLs to import (GitHub/ADO)
- `--backlog-ids-file PATH` - File with backlog item IDs/URLs (one per line or comma-separated)
- `--include-archived/--no-include-archived` - Include archived change proposals in sync (default: False). Useful for updating existing issues with new comment logic or branch detection improvements

**Environment Variables:**

- `GITHUB_TOKEN` - GitHub API token (used if `--github-token` not provided and `--use-gh-cli` is False)

**Watch Mode Features:**

- **Hash-based change detection**: Only processes files that actually changed (SHA256 hash verification)
- **Real-time monitoring**: Automatically detects file changes in tool artifacts, SpecFact bundles, and repository code
- **Dependency tracking**: Tracks file dependencies for incremental processing
- **Debouncing**: Prevents rapid file change events (500ms debounce interval)
- **Change type detection**: Automatically detects whether changes are in tool artifacts, SpecFact bundles, or code
- **LZ4 cache compression**: Faster cache I/O when LZ4 is available (optional)
- **Graceful shutdown**: Press Ctrl+C to stop watch mode cleanly
- **Resource efficient**: Minimal CPU/memory usage

**Examples:**

```bash
# One-time bidirectional sync with Spec-Kit
specfact sync bridge --adapter speckit --repo . --bundle my-project --bidirectional

# Auto-detect adapter and bundle
specfact sync bridge --repo . --bidirectional

# Overwrite tool artifacts with SpecFact bundle
specfact sync bridge --adapter speckit --repo . --bundle my-project --bidirectional --overwrite

# Continuous watch mode
specfact sync bridge --adapter speckit --repo . --bundle my-project --bidirectional --watch --interval 5

# OpenSpec read-only sync (Phase 1 - import only)
specfact sync bridge --adapter openspec --mode read-only --bundle my-project --repo .

# OpenSpec cross-repository sync (OpenSpec in different repo)
specfact sync bridge --adapter openspec --mode read-only --bundle my-project --repo . --external-base-path ../specfact-cli-internal
```

**Backlog Adapter Examples:**

**GitHub Issues:**

```bash
# Bidirectional sync with GitHub Issues (import AND export)
specfact sync bridge --adapter github --bidirectional \
  --repo-owner your-org --repo-name your-repo

# Export OpenSpec change proposals to GitHub issues (auto-detect sanitization)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner owner --repo-name repo

# Export with explicit repository and sanitization

specfact sync bridge --adapter github --mode export-only \
  --repo-owner owner --repo-name repo \
  --sanitize \
  --target-repo public-owner/public-repo

# Export without sanitization (use full proposal content)

specfact sync bridge --adapter github --mode export-only \
  --no-sanitize

# Export using GitHub CLI for token (enterprise-friendly)

specfact sync bridge --adapter github --mode export-only \
  --use-gh-cli

# Export specific change proposals only

specfact sync bridge --adapter github --mode export-only \
  --repo-owner owner --repo-name repo \
  --change-ids add-feature-x,update-api \
  --repo /path/to/openspec-repo

# Update existing GitHub issue (when proposal already linked via source_tracking)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner owner --repo-name repo \
  --change-ids implement-adapter-enhancement-recommendations \
  --update-existing \
  --repo /path/to/openspec-repo

# Update archived change proposals with new comment logic and branch detection
specfact sync bridge --adapter github --mode export-only \
  --repo-owner owner --repo-name repo \
  --include-archived \
  --update-existing \
  --repo /path/to/openspec-repo

# Update specific archived change proposal
specfact sync bridge --adapter github --mode export-only \
  --repo-owner owner --repo-name repo \
  --change-ids add-code-change-tracking \
  --include-archived \
  --update-existing \
  --repo /path/to/openspec-repo

```

**What it syncs (Spec-Kit adapter):**

- `specs/[###-feature-name]/spec.md`, `plan.md`, `tasks.md` ↔ `.specfact/projects/<bundle-name>/bundle.yaml`
- `.specify/memory/constitution.md` ↔ SpecFact business context
- `specs/[###-feature-name]/research.md`, `data-model.md`, `quickstart.md` ↔ SpecFact supporting artifacts
- `specs/[###-feature-name]/contracts/*.yaml` ↔ SpecFact protocol definitions
- Automatic conflict resolution with priority rules

**Spec-Kit Field Auto-Generation:**

When syncing from SpecFact to Spec-Kit (`--bidirectional`), the CLI automatically generates all required Spec-Kit fields:

- **spec.md**: Frontmatter (Feature Branch, Created date, Status), INVSEST criteria, Scenarios (Primary, Alternate, Exception, Recovery)
- **plan.md**: Constitution Check (Article VII, VIII, IX), Phases (Phase 0, 1, 2, -1), Technology Stack (from constraints), Constraints, Unknowns
- **tasks.md**: Phase organization (Phase 1: Setup, Phase 2: Foundational, Phase 3+: User Stories), Story mappings ([US1], [US2]), Parallel markers [P]

**All Spec-Kit fields are auto-generated** - no manual editing required unless you want to customize defaults. Generated artifacts are ready for `/speckit.analyze` without additional work.

**Content Sanitization (export-only mode):**

When exporting OpenSpec change proposals to public repositories, content sanitization removes internal/competitive information while preserving user-facing value:

**What's Removed:**

- Competitive analysis sections
- Market positioning statements
- Implementation details (file-by-file changes)
- Effort estimates and timelines
- Technical architecture details
- Internal strategy sections

**What's Preserved:**

- High-level feature descriptions
- User-facing value propositions
- Acceptance criteria
- External documentation links
- Use cases and examples

**When to Use Sanitization:**

- **Different repos** (code repo ≠ planning repo): Sanitization recommended (default: yes)
- **Same repo** (code repo = planning repo): Sanitization optional (default: no, user can override)
- **Breaking changes**: Use sanitization to communicate changes early without exposing internal strategy
- **OSS collaboration**: Use sanitization for public issues to keep contributors informed

**Sanitization Auto-Detection:**

- Automatically detects if code and planning are in different repositories
- Defaults to sanitize when repos differ (protects internal information)
- Defaults to no sanitization when repos are the same (user can choose full disclosure)
- User can override with `--sanitize` or `--no-sanitize` flags

**AI-Assisted Sanitization:**

- Use slash command `/specfact.sync-backlog` for interactive, AI-assisted content rewriting
- AI analyzes proposal content and suggests sanitized version
- User can review and approve sanitized content before issue creation
- Useful for complex proposals requiring nuanced content adaptation

**Proposal Filtering (export-only mode):**

When exporting OpenSpec change proposals to DevOps tools, proposals are filtered based on target repository type and status:

**Public Repositories** (with `--sanitize`):

- **Only syncs proposals with status `"applied"`** (archived/completed changes)
- Filters out proposals with status `"proposed"`, `"in-progress"`, `"deprecated"`, or `"discarded"`
- Applies regardless of whether proposals have existing source tracking entries
- Prevents premature exposure of work-in-progress proposals to public repositories
- Warning message displayed when proposals are filtered out

**Internal Repositories** (with `--no-sanitize` or auto-detected as internal):

- Syncs all active proposals regardless of status:
  - `"proposed"` - New proposals not yet started
  - `"in-progress"` - Proposals currently being worked on
  - `"applied"` - Completed/archived proposals
  - `"deprecated"` - Deprecated proposals
  - `"discarded"` - Discarded proposals
- If proposal has source tracking entry for target repo: syncs it (for updates)
- If proposal doesn't have entry: syncs if status is active

**Examples:**

```bash
# Public repo: only syncs "applied" proposals (archived changes)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli \
  --sanitize \
  --target-repo nold-ai/specfact-cli

# Internal repo: syncs all active proposals (proposed, in-progress, applied, etc.)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli-internal \
  --no-sanitize \
  --target-repo nold-ai/specfact-cli-internal
```

**Code Change Tracking and Progress Comments (export-only mode):**

When using `--mode export-only` with DevOps adapters, you can track implementation progress by detecting code changes and adding progress comments to existing GitHub issues:

**Advanced Options** (hidden by default, use `--help-advanced` or `-ha` to view):

- `--track-code-changes/--no-track-code-changes` - Detect code changes (git commits, file modifications) and add progress comments to existing issues (default: False)
- `--add-progress-comment/--no-add-progress-comment` - Add manual progress comment to existing issues without code change detection (default: False)
- `--code-repo PATH` - Path to source code repository for code change detection (default: same as `--repo`). **Required when OpenSpec repository differs from source code repository.** For example, if OpenSpec proposals are in `specfact-cli-internal` but source code is in `specfact-cli`, use `--repo /path/to/specfact-cli-internal --code-repo /path/to/specfact-cli`.
- `--update-existing/--no-update-existing` - Update existing issue bodies when proposal content changes (default: False for safety). Uses content hash to detect changes.

**Code Change Detection:**

When `--track-code-changes` is enabled:

1. **Git Commit Detection**: Searches git log for commits mentioning the change proposal ID (e.g., `add-code-change-tracking`)
2. **File Change Tracking**: Extracts files modified in detected commits
3. **Progress Comment Generation**: Formats progress comment with:
   - Commit details (hash, message, author, date)
   - Files changed summary
   - Detection timestamp
4. **Duplicate Prevention**: Calculates SHA-256 hash of comment text and checks against existing progress comments
5. **Source Tracking Update**: Stores progress comment in `source_metadata.progress_comments` and updates `last_code_change_detected` timestamp

**Progress Comment Sanitization:**

When `--sanitize` is enabled (for public repositories), progress comments are automatically sanitized:

- **Commit messages**: Internal/confidential/competitive keywords removed, long messages truncated
- **File paths**: Replaced with file type counts (e.g., "3 py file(s)" instead of full paths)
- **Author emails**: Removed, only username shown
- **Timestamps**: Date only (no time component)

**Examples:**

```bash
# Detect code changes and add progress comments (internal repo)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli-internal \
  --track-code-changes \
  --repo .

# Detect code changes with sanitization (public repo)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli \
  --track-code-changes \
  --sanitize \
  --repo .

# Add manual progress comment (without code change detection)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli-internal \
  --add-progress-comment \
  --repo .

# Update existing issues AND add progress comments
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli-internal \
  --update-existing \
  --track-code-changes \
  --repo .

# Sync specific change proposal with code change tracking
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli-internal \
  --track-code-changes \
  --change-ids add-code-change-tracking \
  --repo .

# Separate OpenSpec and source code repositories
# OpenSpec proposals in specfact-cli-internal, source code in specfact-cli
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli-internal \
  --track-code-changes \
  --change-ids add-code-change-tracking \
  --repo /path/to/specfact-cli-internal \
  --code-repo /path/to/specfact-cli
```

**Prerequisites:**

**For Issue Creation:**

- Change proposals must exist in `openspec/changes/<change-id>/proposal.md` directory (in the OpenSpec repository specified by `--repo`)
- GitHub token (via `GITHUB_TOKEN` env var, `gh auth token`, or `--github-token`)
- Repository access permissions (read for proposals, write for issues)

**For Code Change Tracking:**

- Issues must already exist (created via previous sync)
- Git repository with commits mentioning the change proposal ID in commit messages:
  - If `--code-repo` is provided, commits must be in that repository
  - Otherwise, commits must be in the OpenSpec repository (`--repo`)
- Commit messages should include the change proposal ID (e.g., "feat: implement add-code-change-tracking")

**Separate OpenSpec and Source Code Repositories:**

When your OpenSpec change proposals are in a different repository than your source code:

```bash
# Example: OpenSpec in specfact-cli-internal, source code in specfact-cli
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli-internal \
  --track-code-changes \
  --repo /path/to/specfact-cli-internal \
  --code-repo /path/to/specfact-cli
```

**Why use `--code-repo`?**

- **OpenSpec repository** (`--repo`): Contains change proposals in `openspec/changes/` directory
- **Source code repository** (`--code-repo`): Contains actual implementation commits that reference the change proposal ID

If both are in the same repository, you can omit `--code-repo` and it will use `--repo` for both purposes.

**Integration Workflow:**

1. **Initial Setup** (one-time):

   ```bash
   # Create change proposal in openspec/changes/<change-id>/proposal.md
   # Export to GitHub to create issue
   specfact sync bridge --adapter github --mode export-only \
     --repo-owner owner --repo-name repo \
     --repo /path/to/openspec-repo
   ```

2. **Development Workflow** (ongoing):

   ```bash
   # Make commits with change ID in commit message
   git commit -m "feat: implement add-code-change-tracking - initial implementation"
   
   # Track progress automatically
   specfact sync bridge --adapter github --mode export-only \
     --repo-owner owner --repo-name repo \
     --track-code-changes \
     --repo /path/to/openspec-repo \
     --code-repo /path/to/source-code-repo
   ```

3. **Manual Progress Updates** (when needed):

   ```bash
   # Add manual progress comment without code change detection
   specfact sync bridge --adapter github --mode export-only \
     --repo-owner owner --repo-name repo \
     --add-progress-comment \
     --repo /path/to/openspec-repo
   ```

**Verification:**

After running the command, verify:

1. **GitHub Issue**: Check that progress comment was added to the issue:

   ```bash
   gh issue view <issue-number> --repo owner/repo --json comments --jq '.comments[-1].body'
   ```

2. **Source Tracking**: Verify `openspec/changes/<change-id>/proposal.md` was updated with:

   ```markdown
   ## Source Tracking
   
   - **GitHub Issue**: #123
   - **Issue URL**: <https://github.com/owner/repo/issues/123>
   - **Last Synced Status**: proposed
   - **Sanitized**: false
   <!-- last_code_change_detected: 2025-12-30T10:00:00Z -->
   ```

3. **Duplicate Prevention**: Run the same command twice - second run should skip duplicate comment (no new comment added)

**Troubleshooting:**

- **No commits detected**: Ensure commit messages include the change proposal ID (e.g., "add-code-change-tracking")
- **Wrong repository**: Verify `--code-repo` points to the correct source code repository
- **No comments added**: Check that issues exist (create them first without `--track-code-changes`)
- **Sanitization issues**: Use `--sanitize` for public repos, `--no-sanitize` for internal repos

**Constitution Evidence Extraction:**

When generating Spec-Kit `plan.md` files, SpecFact automatically extracts evidence-based constitution alignment from your codebase:

- **Article VII (Simplicity)**: Analyzes project structure, directory depth, file organization, and naming patterns to determine PASS/FAIL status with rationale
- **Article VIII (Anti-Abstraction)**: Detects framework usage, abstraction layers, and framework-specific patterns to assess anti-abstraction compliance
- **Article IX (Integration-First)**: Analyzes contract patterns (icontract decorators, OpenAPI definitions, type hints) to verify integration-first approach

**Evidence-Based Status**: Constitution check sections include PASS/FAIL status (not PENDING) with:

- Evidence citations from code patterns
- Rationale explaining why each article passes or fails
- Actionable recommendations for improvement (if FAIL)

This evidence extraction happens automatically during `sync bridge --adapter speckit` when generating Spec-Kit artifacts. No additional configuration required.

#### `sync repository`

Sync code changes to SpecFact artifacts:

```bash
specfact sync repository [OPTIONS]
```

**Options:**

- `--repo PATH` - Path to repository (default: `.`)
- `--target PATH` - Target directory for artifacts (default: `.specfact`)
- `--watch` - Watch mode for continuous sync (monitors code changes in real-time)

**Advanced Options** (hidden by default, use `--help-advanced` or `-ha` to view):

- `--interval INT` - Watch interval in seconds (default: 5, minimum: 1)
- `--confidence FLOAT` - Minimum confidence threshold for feature detection (default: 0.5, range: 0.0-1.0)

**Watch Mode Features:**

- **Hash-based change detection**: Only processes files that actually changed (SHA256 hash verification)
- **Real-time monitoring**: Automatically detects code changes in repository
- **Automatic sync**: Triggers sync when code changes are detected
- **Deviation tracking**: Tracks deviations from manual plans as code changes
- **Dependency tracking**: Tracks file dependencies for incremental processing
- **Debouncing**: Prevents rapid file change events (500ms debounce interval)
- **LZ4 cache compression**: Faster cache I/O when LZ4 is available (optional)
- **Graceful shutdown**: Press Ctrl+C to stop watch mode cleanly

**Example:**

```bash
# One-time sync
specfact sync repository --repo . --target .specfact

# Continuous watch mode (monitors for code changes every 5 seconds)
specfact sync repository --repo . --watch --interval 5

# Watch mode with custom interval and confidence threshold
specfact sync repository --repo . --watch --interval 2 --confidence 0.7
```

**What it tracks:**

- Code changes → Plan artifact updates
- Deviations from manual plans
- Feature/story extraction from code

---

### `backlog` - Backlog Refinement and Template Management

Backlog refinement commands for AI-assisted template-driven refinement of DevOps backlog items.

**Command Topology (recommended):**

- `specfact backlog ceremony standup ...`
- `specfact backlog ceremony refinement ...`
- `specfact backlog delta status|impact|cost-estimate|rollback-analysis ...`
- `specfact backlog analyze-deps|trace-impact|sync|verify-readiness|diff|promote|generate-release-notes ...`

Compatibility commands `specfact backlog daily` and `specfact backlog refine` remain available, but ceremony entrypoints are preferred for discoverability.

#### `backlog ceremony`

Ceremony-oriented entrypoint group for event-driven backlog workflows.

```bash
specfact backlog ceremony [OPTIONS] COMMAND [ARGS]...
```

**Subcommands:**

- `standup` - Preferred standup command (delegates to daily workflow implementation)
- `refinement` - Preferred refinement command (delegates to refine workflow implementation)
- `planning` - Planning alias (when planning module delegate is installed)
- `flow` - Flow-view alias (when flow delegate is installed)
- `pi-summary` - PI summary alias (when PI delegate is installed)

**Examples:**

```bash
specfact backlog ceremony standup github --state open --limit 20
specfact backlog ceremony refinement github --search "is:open label:feature" --preview
```

#### `backlog delta`

Delta analysis commands for backlog graph drift and impact tracking.

```bash
specfact backlog delta [OPTIONS] COMMAND [ARGS]...
```

**Subcommands:**

- `status` - Compare current graph vs baseline and summarize changes
- `impact` - Analyze downstream impact from one item
- `cost-estimate` - Estimate delta effort points from graph changes
- `rollback-analysis` - Assess rollback risk from removed items/dependencies

**Examples:**

```bash
specfact backlog delta status --project-id 1 --adapter github
specfact backlog delta impact 123 --project-id 1 --adapter github
specfact backlog delta cost-estimate --project-id 1 --adapter github
specfact backlog delta rollback-analysis --project-id 1 --adapter github
```

#### `backlog analyze-deps`

Build and analyze backlog dependency graph for a provider project.

```bash
specfact backlog analyze-deps --project-id <id> [OPTIONS]
```

**Common options:**

- `--adapter ADAPTER` - Backlog adapter id (default: `github`)
- `--template TEMPLATE` - Mapping template (default: `github_projects`)
- `--custom-config PATH` - Optional custom mapping YAML
- `--output PATH` - Optional markdown summary output
- `--json-export PATH` - Optional graph JSON export

#### `backlog trace-impact`

Trace direct and transitive dependency impact for a backlog item.

```bash
specfact backlog trace-impact <item-id> --project-id <id> [OPTIONS]
```

**Common options:**

- `--adapter ADAPTER` - Backlog adapter id (default: `github`)
- `--template TEMPLATE` - Mapping template (default: `github_projects`)
- `--custom-config PATH` - Optional custom mapping YAML

#### `backlog verify-readiness`

Verify release readiness using dependency/cycle/blocker and status checks.

```bash
specfact backlog verify-readiness --project-id <id> [OPTIONS]
```

**Common options:**

- `--adapter ADAPTER` - Backlog adapter id (default: `github`)
- `--template TEMPLATE` - Mapping template (default: `github_projects`)
- `--target-items CSV` - Optional comma-separated subset of item IDs

#### `backlog diff`

Compare current backlog graph to baseline and print graph delta.

```bash
specfact backlog diff --project-id <id> [OPTIONS]
```

#### `backlog sync`

Sync backlog graph projection (for example to plan-oriented output formats).

```bash
specfact backlog sync --project-id <id> [OPTIONS]
```

#### `backlog promote`

Promote backlog graph state into structured promotion artifacts.

```bash
specfact backlog promote --project-id <id> [OPTIONS]
```

#### `backlog generate-release-notes`

Generate release notes from backlog dependency/graph context.

```bash
specfact backlog generate-release-notes --project-id <id> [OPTIONS]
```

#### `backlog refine`

Refine backlog items using AI-assisted template matching. Transforms arbitrary DevOps backlog input (GitHub Issues, ADO work items) into structured, template-compliant format (user stories, defects, spikes, enablers).

Preferred entrypoint for team-facing docs is `specfact backlog ceremony refinement ...`. This section documents the underlying compatibility command surface.

```bash
specfact backlog refine <ADAPTER> [OPTIONS]
```

**Arguments:**

- `ADAPTER` - Backlog adapter name (`github`, `ado`, etc.)

**Options:**

**Filtering Options:**

- `--labels`, `--tags` - Filter by labels/tags (can specify multiple, e.g., `--labels feature,enhancement`)
- `--state` - Filter by state (e.g., `open`, `closed`, `active`)
- `--assignee` - Filter by assignee username
- `--iteration` - Filter by iteration path (ADO format: `Project\\Sprint 1`)
- `--sprint` - Filter by sprint identifier
- `--release` - Filter by release identifier
- `--persona` - Filter templates by persona (`product-owner`, `architect`, `developer`)
- `--framework` - Filter templates by framework (`agile`, `scrum`, `safe`, `kanban`)
- `--search`, `-s` - Generic search query using provider-specific syntax (e.g., GitHub: `is:open label:feature`)

**Template Selection:**

- `--template`, `-t` - Target template ID (default: auto-detect with priority-based resolution)

**Refinement Options:**

- `--auto-accept-high-confidence` - Auto-accept refinements with confidence >= 0.85

**Preview and Writeback:**

- `--preview` / `--no-preview` - Preview mode: show what will be written without updating backlog (default: `--preview`)
- `--write` - Write mode: explicitly opt-in to update remote backlog (requires `--write` flag)
- During `--write`, structured refinement output is parsed into canonical fields before adapter updates.
  - Supports markdown headings and label-style sections (for example `Description:`, `Acceptance Criteria:`, `Story Points:`).
  - ADO updates mapped fields separately (description, acceptance criteria, metrics) instead of writing label blocks verbatim to description.
  - GitHub keeps field updates consistent even when refined body contains headings that omit some core field sections.

**Definition of Ready (DoR):**

- `--check-dor` - Check Definition of Ready (DoR) rules before refinement (loads from `.specfact/dor.yaml`)

**OpenSpec Integration:**

- `--bundle`, `-b` - OpenSpec bundle path to import refined items
- `--auto-bundle` - Auto-import refined items to OpenSpec bundle
- `--openspec-comment` - Add OpenSpec change proposal reference as comment (preserves original body)

**Adapter Configuration:**

**GitHub Adapter:**

- `--repo-owner` - GitHub repository owner (required for GitHub adapter)
- `--repo-name` - GitHub repository name (required for GitHub adapter)
- `--github-token` - GitHub API token (optional, uses GITHUB_TOKEN env var or gh CLI if not provided)

**Azure DevOps Adapter:**

- `--ado-org` - Azure DevOps organization or collection name (required for ADO adapter, except when collection is in base_url)
- `--ado-project` - Azure DevOps project (required for ADO adapter)
- `--ado-base-url` - Azure DevOps base URL (optional, defaults to `https://dev.azure.com` for cloud)
  - **Cloud**: `https://dev.azure.com` (default)
  - **On-premise**: `https://server` or `https://server/tfs/collection` (if collection included)
- `--ado-token` - Azure DevOps PAT (optional, uses AZURE_DEVOPS_TOKEN env var or stored token if not provided)

**ADO Configuration Notes:**

- **Cloud (Azure DevOps Services)**: Always requires `--ado-org` and `--ado-project`. Base URL defaults to `https://dev.azure.com`.
- **On-premise (Azure DevOps Server)**:
  - If base URL includes collection (e.g., `https://server/tfs/DefaultCollection`), `--ado-org` is optional.
  - If base URL doesn't include collection, provide collection name via `--ado-org`.
- **API Endpoints**:
  - WIQL queries use POST to `{base_url}/{org}/{project}/_apis/wit/wiql?api-version=7.1`
  - Work items batch GET uses `{base_url}/{org}/_apis/wit/workitems?ids={ids}&api-version=7.1` (organization-level, not project-level)

**Architecture Note**: SpecFact CLI follows a CLI-first architecture:

- SpecFact CLI generates prompts/instructions for IDE AI copilots (Cursor, Claude Code, etc.)
- IDE AI copilots execute those instructions using their native LLM
- IDE AI copilots feed results back to SpecFact CLI
- SpecFact CLI validates and processes the results
- SpecFact CLI does NOT directly invoke LLM APIs (OpenAI, Anthropic, etc.)

**Examples:**

```bash
# Refine GitHub issues (auto-detect template)
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --state open

# Refine GitHub issues with search query
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --search "is:open label:feature"

# Filter by labels and state
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --labels feature,enhancement --state open

# Filter by sprint and assignee
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --sprint "Sprint 1" --assignee dev1

# Filter by framework and persona (Scrum + Product Owner)
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --framework scrum --persona product-owner --labels feature

# Refine with specific template
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --template user_story_v1 --state open

# Check Definition of Ready before refinement
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --check-dor --labels feature

# Preview refinement without writing (default)
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --preview --labels feature

# Write refinement to backlog (explicit opt-in)
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --write --labels feature

# Auto-accept high-confidence refinements
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --auto-accept-high-confidence --state open

# Refine and import to OpenSpec bundle
specfact backlog refine github \
  --repo-owner "nold-ai" \
  --repo-name "specfact-cli" \
  --bundle my-project \
  --auto-bundle \
  --state open

# Refine and add OpenSpec comment (preserves original body)
specfact backlog refine github --repo-owner "nold-ai" --repo-name "specfact-cli" --write --openspec-comment --state open

# Refine ADO work items (Azure DevOps Services - cloud)
specfact backlog refine ado \
  --ado-org "my-org" \
  --ado-project "my-project" \
  --state Active

# Refine ADO work items (Azure DevOps Server - on-premise, collection in base_url)
specfact backlog refine ado \
  --ado-base-url "https://devops.company.com/tfs/DefaultCollection" \
  --ado-project "my-project" \
  --state Active

# Refine ADO work items (Azure DevOps Server - on-premise, collection provided)
specfact backlog refine ado \
  --ado-base-url "https://devops.company.com" \
  --ado-org "DefaultCollection" \
  --ado-project "my-project" \
  --state Active

# Refine ADO work items with sprint filter
specfact backlog refine ado \
  --ado-org "my-org" \
  --ado-project "my-project" \
  --sprint "Sprint 1" \
  --state Active

# Refine ADO work items with iteration path
specfact backlog refine ado \
  --ado-org "my-org" \
  --ado-project "my-project" \
  --iteration "Project\\Release 1\\Sprint 1"
```

**Pre-built Templates:**

- `user_story_v1` - User story format (As a / I want / So that / Acceptance Criteria)
- `defect_v1` - Defect/bug format (Summary / Steps to Reproduce / Expected / Actual / Environment)
- `spike_v1` - Research spike format (Research Question / Approach / Findings / Recommendation)
- `enabler_v1` - Enabler work format (Description / Dependencies / Implementation / Success Criteria)

**Command Chaining**: The `backlog refine` command is designed to work seamlessly with `sync bridge`:

```bash
# Refine backlog items, then sync to external tool
specfact backlog refine github --repo-owner "my-org" --repo-name "my-repo" --write --labels feature
specfact sync bridge --adapter github --repo-owner "my-org" --repo-name "my-repo" --backlog-ids 123,456

# Cross-adapter sync: Refine from GitHub → Sync to ADO (with automatic state mapping)
specfact backlog refine github --repo-owner "my-org" --repo-name "my-repo" --write --labels feature
specfact sync bridge --adapter ado --ado-org "my-org" --ado-project "my-project" --backlog-ids 123,456 --mode bidirectional
# State is automatically mapped: GitHub "open" → ADO "New", GitHub "closed" → ADO "Closed"
```

**Cross-Adapter State Mapping**:

When syncing backlog items between different adapters (e.g., GitHub ↔ ADO), the system automatically preserves and maps states using a generic mechanism:

- **State Preservation**: Original `source_state` is stored in bundle entries during import and used during cross-adapter export to ensure accurate state translation
- **Generic Mapping**: Uses OpenSpec as intermediate format:
  - Source adapter state → OpenSpec status → Target adapter state
- **Bidirectional**: Works in both directions (GitHub → ADO and ADO → GitHub)
- **Automatic**: No manual configuration required - state mapping is automatic when `source_state` and `source_type` are present in bundle entries

**State Mapping Examples**:

- GitHub "open" ↔ ADO "New" (active work)
- GitHub "closed" ↔ ADO "Closed" (completed work)
- ADO "Active" → GitHub "open" (active work remains open)
- ADO "Resolved" → GitHub "closed" (resolved work is closed)

**State Preservation Guarantees**:

- Original backlog state is preserved in `source_metadata["source_state"]` during import
- State is automatically mapped during cross-adapter export using generic mapping mechanism
- Ensures closed items remain closed and open items remain open across adapter boundaries
- No data loss - original state information is preserved throughout the sync process

**ADO Adapter Configuration**:

The Azure DevOps adapter supports both **Azure DevOps Services (cloud)** and **Azure DevOps Server (on-premise)**:

**Cloud Configuration** (Azure DevOps Services):

```bash
specfact backlog refine ado \
  --ado-org "my-org" \
  --ado-project "my-project" \
  --state Active
```

- Base URL: `https://dev.azure.com` (default)
- URL Format: `https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version=7.1`

**On-Premise Configuration** (Azure DevOps Server):

```bash
# Option 1: Collection in base URL
specfact backlog refine ado \
  --ado-base-url "https://devops.company.com/tfs/DefaultCollection" \
  --ado-project "my-project" \
  --state Active

# Option 2: Collection provided separately
specfact backlog refine ado \
  --ado-base-url "https://devops.company.com" \
  --ado-org "DefaultCollection" \
  --ado-project "my-project" \
  --state Active
```

- Base URL: Your on-premise server URL
- URL Format: `https://server/tfs/collection/{project}/_apis/wit/wiql?api-version=7.1` or `https://server/collection/{project}/_apis/wit/wiql?api-version=7.1`

**ADO API Endpoint Requirements**:

- **WIQL Query**: POST to `{base_url}/{org}/{project}/_apis/wit/wiql?api-version=7.1` (project-level endpoint)
- **Work Items Batch GET**: GET to `{base_url}/{org}/_apis/wit/workitems?ids={ids}&api-version=7.1` (organization-level endpoint)
- **api-version Parameter**: Required for all ADO API calls (default: `7.1`)

**Preview Output Features**:

- **Progress Indicators**: Shows detailed progress during initialization (templates, detector, AI refiner, adapter, DoR config, validation)
- **Required Fields Always Displayed**: All required fields from the template are always shown, even when empty, with `(empty - required field)` indicator to help copilot identify missing elements
- **Assignee Display**: Always shows assignee(s) or "Unassigned" status
- **Acceptance Criteria Display**: Always shows acceptance criteria if required by template (even when empty)

#### `backlog map-fields`

Interactively map Azure DevOps fields to canonical field names. This command helps you discover available ADO fields and create custom field mappings for your specific ADO process template.

```bash
specfact backlog map-fields [OPTIONS]
```

**Options:**

- `--ado-org` - Azure DevOps organization or collection name (required)
- `--ado-project` - Azure DevOps project (required)
- `--ado-token` - Azure DevOps PAT (optional, uses token resolution priority: explicit > env var > stored token)
- `--ado-base-url` - Azure DevOps base URL (optional, defaults to `https://dev.azure.com`)
- `--reset` - Reset custom field mapping to defaults (deletes `ado_custom.yaml` and restores default mappings)

**Token Resolution Priority:**

1. Explicit `--ado-token` parameter
2. `AZURE_DEVOPS_TOKEN` environment variable
3. Stored token via `specfact auth azure-devops`
4. Expired stored token (shows warning with options to refresh)

**Features:**

- **Interactive Menu**: Uses arrow-key navigation (↑↓ to navigate, Enter to select) similar to `openspec archive`
- **Default Pre-population**: Automatically pre-populates default mappings from `AdoFieldMapper.DEFAULT_FIELD_MAPPINGS`
- **Smart Field Preference**: Prefers `Microsoft.VSTS.Common.*` fields over `System.*` fields for better compatibility
- **Fuzzy Matching**: Uses regex/fuzzy matching to suggest potential matches when no default mapping exists
- **Pre-selection**: Automatically pre-selects best match (existing custom > default > fuzzy match > "<no mapping>")
- **Automatic Usage**: Custom mappings are automatically used by all subsequent backlog operations in that directory (no restart needed)

**Examples:**

```bash
# Interactive mapping (uses stored token automatically)
specfact backlog map-fields --ado-org myorg --ado-project myproject

# Override with explicit token
specfact backlog map-fields --ado-org myorg --ado-project myproject --ado-token your_token

# Reset to default mappings
specfact backlog map-fields --ado-org myorg --ado-project myproject --reset
```

**Output Location:**

Mappings are saved to `.specfact/templates/backlog/field_mappings/ado_custom.yaml` and automatically detected by `AdoFieldMapper` for all subsequent operations.

**See Also**: [Custom Field Mapping Guide](../guides/custom-field-mapping.md) for complete documentation on field mapping templates and best practices.

**ADO Troubleshooting**:

**Error: "No HTTP resource was found that matches the request URI"**

- **Cause**: Missing `api-version` parameter or incorrect URL format
- **Solution**: Ensure `api-version=7.1` is included in all ADO API URLs. Check base URL format for on-premise installations.

**Error: "The requested resource does not support http method 'GET'"**

- **Cause**: Attempting to use GET on WIQL endpoint (which requires POST)
- **Solution**: WIQL queries must use POST method with JSON body containing the query.

**Error: Organization removed from request string**

- **Cause**: Incorrect base URL format (may already include organization/collection)
- **Solution**: For on-premise, check if base URL already includes collection. If yes, omit `--ado-org` or adjust base URL.

**See**: [Backlog Refinement Guide](../guides/backlog-refinement.md) for complete documentation including command chaining workflows and ADO adapter configuration details.

---

### `validate` - Validation Commands

Validation commands for contract-based validation of codebases.

#### `validate sidecar`

Sidecar validation enables contract-based validation of external codebases without modifying source code.

**Subcommands:**

- `validate sidecar init` - Initialize sidecar workspace
- `validate sidecar run` - Run sidecar validation workflow

**See**: [Sidecar Validation Guide](../guides/sidecar-validation.md) for complete documentation.

##### `validate sidecar init`

Initialize sidecar workspace for validation.

```bash
specfact validate sidecar init <bundle-name> <repo-path>
```

**Arguments:**

- `bundle-name` - Project bundle name (e.g., 'legacy-api')
- `repo-path` - Path to repository root directory

**What it does:**

- Detects framework type (Django, FastAPI, DRF, Flask, pure-python)
- Creates sidecar workspace directory structure
- Generates configuration files
- Detects Python environment (venv, poetry, uv, pip)
- Sets up framework-specific configuration (e.g., DJANGO_SETTINGS_MODULE)

**Example:**

```bash
specfact validate sidecar init legacy-api /path/to/django-project
```

##### `validate sidecar run`

Run sidecar validation workflow.

```bash
specfact validate sidecar run <bundle-name> <repo-path> [OPTIONS]
```

**Arguments:**

- `bundle-name` - Project bundle name (e.g., 'legacy-api')
- `repo-path` - Path to repository root directory

**Options:**

- `--run-crosshair / --no-run-crosshair` - Run CrossHair symbolic execution analysis (default: enabled)
- `--run-specmatic / --no-run-specmatic` - Run Specmatic contract testing validation (default: enabled, auto-skipped if no service configuration detected)

**Auto-Skip Behavior:**

Specmatic is automatically skipped when no service configuration is detected (no `test_base_url`, `host`/`port`, or application server configuration). Use `--run-specmatic` to force execution or configure a service endpoint to enable Specmatic validation.

**Workflow steps:**

1. Framework detection (Django, FastAPI, DRF, Flask, pure-python)
2. Dependency installation in isolated venv (`.specfact/venv/`) with framework and project dependencies
3. Route extraction from framework-specific patterns (all HTTP methods captured for Flask)
4. Contract population with extracted routes/schemas (expected status codes and response structure validation)
5. Harness generation from populated contracts
6. CrossHair analysis on source code and harness (if enabled, using venv Python)
7. Specmatic validation against API endpoints (if enabled)

**Example:**

```bash
# Run full validation (CrossHair + Specmatic)
specfact validate sidecar run legacy-api /path/to/django-project

# Run only CrossHair analysis
specfact validate sidecar run legacy-api /path/to/django-project --no-run-specmatic

# Run only Specmatic validation
specfact validate sidecar run legacy-api /path/to/django-project --no-run-crosshair

# Force Specmatic to run even without service configuration (may fail)
specfact validate sidecar run legacy-api /path/to/django-project --run-specmatic
```

**Output:**

- Validation results displayed in console
- Reports saved to `.specfact/projects/<bundle>/reports/sidecar/`
- Progress indicators for long-running operations

**Supported Frameworks:**

- **Django**: Extracts URL patterns and form schemas
- **FastAPI**: Extracts routes and Pydantic models
- **DRF**: Extracts serializers and converts to OpenAPI
- **Flask**: Extracts routes from `@app.route()` and `@bp.route()` decorators, captures all HTTP methods, preserves parameter names for converter-based paths
- **Pure Python**: Basic function extraction (if runtime contracts present)

**See**: [Sidecar Validation Guide](../guides/sidecar-validation.md) for detailed documentation and examples.

### `spec` - API Specification Management (Specmatic Integration)

Manage API specifications with Specmatic for OpenAPI/AsyncAPI validation, backward compatibility checking, and mock server functionality.

**Note**: Specmatic is a Java CLI tool that must be installed separately from [https://docs.specmatic.io/](https://docs.specmatic.io/). SpecFact CLI will check for Specmatic availability and provide helpful error messages if it's not found.

#### `spec validate`

Validate OpenAPI/AsyncAPI specification using Specmatic. Can validate a single file or all contracts in a project bundle.

```bash
specfact spec validate [<spec-path>] [OPTIONS]
```

**Arguments:**

- `<spec-path>` - Path to OpenAPI/AsyncAPI specification file (optional if --bundle provided)

**Options:**

- `--bundle NAME` - Project bundle name (e.g., legacy-api). If provided, validates all contracts in bundle. Default: active plan from 'specfact plan select'
- `--previous PATH` - Path to previous version for backward compatibility check
- `--no-interactive` - Non-interactive mode (for CI/CD automation). Disables interactive prompts.

**Examples:**

```bash
# Validate a single spec file
specfact spec validate api/openapi.yaml

# With backward compatibility check
specfact spec validate api/openapi.yaml --previous api/openapi.v1.yaml

# Validate all contracts in active bundle (interactive selection)
specfact spec validate

# Validate all contracts in specific bundle
specfact spec validate --bundle legacy-api

# Non-interactive: validate all contracts
specfact spec validate --bundle legacy-api --no-interactive
```

**CLI-First Pattern**: Uses active plan (from `specfact plan select`) as default, or specify `--bundle`. Never requires direct `.specfact` paths - always use the CLI interface. When multiple contracts are available, shows interactive list for selection.

**What it checks:**

- Schema structure validation
- Example generation test
- Backward compatibility (if previous version provided)

**Output:**

- Validation results table with status for each check
- ✓ PASS or ✗ FAIL for each validation step
- Detailed errors if validation fails
- Summary when validating multiple contracts

#### `spec backward-compat`

Check backward compatibility between two spec versions.

```bash
specfact spec backward-compat <old-spec> <new-spec>
```

**Arguments:**

- `<old-spec>` - Path to old specification version (required)
- `<new-spec>` - Path to new specification version (required)

**Example:**

```bash
specfact spec backward-compat api/openapi.v1.yaml api/openapi.v2.yaml
```

**Output:**

- ✓ Compatible - No breaking changes detected
- ✗ Breaking changes - Lists incompatible changes

#### `spec generate-tests`

Generate Specmatic test suite from specification. Can generate for a single file or all contracts in a bundle.

```bash
specfact spec generate-tests [<spec-path>] [OPTIONS]
```

**Arguments:**

- `<spec-path>` - Path to OpenAPI/AsyncAPI specification (optional if --bundle provided)

**Options:**

- `--bundle NAME` - Project bundle name (e.g., legacy-api). If provided, generates tests for all contracts in bundle. Default: active plan from 'specfact plan select'
- `--out PATH` - Output directory for generated tests (default: `.specfact/specmatic-tests/`)

**Examples:**

```bash
# Generate for a single spec file
specfact spec generate-tests api/openapi.yaml

# Generate to custom location
specfact spec generate-tests api/openapi.yaml --out tests/specmatic/

# Generate tests for all contracts in active bundle
specfact spec generate-tests --bundle legacy-api

# Generate tests for all contracts in specific bundle
specfact spec generate-tests --bundle legacy-api --out tests/contract/
```

**CLI-First Pattern**: Uses active plan as default, or specify `--bundle`. Never requires direct `.specfact` paths.

**Caching:**
Test generation results are cached in `.specfact/cache/specmatic-tests.json` based on file content hashes. Unchanged contracts are automatically skipped on subsequent runs. Use `--force` to bypass cache.

**Output:**

- ✓ Test suite generated with path to output directory
- Instructions to run the generated tests
- Summary when generating tests for multiple contracts

**What to Do With Generated Tests:**

The generated tests are executable contract tests that validate your API implementation against the OpenAPI/AsyncAPI specification. Here's how to use them:

1. **Generate tests** (you just did this):

   ```bash
   specfact spec generate-tests --bundle my-api --output tests/contract/
   ```

2. **Start your API server**:

   ```bash
   python -m uvicorn main:app --port 8000
   ```

3. **Run tests against your API**:

   ```bash
   specmatic test \
     --spec .specfact/projects/my-api/contracts/api.openapi.yaml \
     --host http://localhost:8000
   ```

4. **Tests validate**:
   - Request format matches spec (headers, body, query params)
   - Response format matches spec (status codes, headers, body schema)
   - All endpoints are implemented
   - Data types and constraints are respected

**CI/CD Integration:**

```yaml
- name: Generate contract tests
  run: specfact spec generate-tests --bundle my-api --output tests/contract/

- name: Start API server
  run: python -m uvicorn main:app --port 8000 &

- name: Run contract tests
  run: specmatic test --spec ... --host http://localhost:8000
```

See [Specmatic Integration Guide](../guides/specmatic-integration.md#what-can-you-do-with-generated-tests) for complete walkthrough.

#### `spec mock`

Launch Specmatic mock server from specification. Can use a single spec file or select from bundle contracts.

```bash
specfact spec mock [OPTIONS]
```

**Options:**

- `--spec PATH` - Path to OpenAPI/AsyncAPI specification (default: auto-detect from current directory)
- `--bundle NAME` - Project bundle name (e.g., legacy-api). If provided, selects contract from bundle. Default: active plan from 'specfact plan select'
- `--port INT` - Port number for mock server (default: 9000)
- `--strict/--examples` - Use strict validation mode or examples mode (default: strict)
- `--no-interactive` - Non-interactive mode (for CI/CD automation). Uses first contract if multiple available.

**Examples:**

```bash
# Auto-detect spec file from current directory
specfact spec mock

# Specify spec file and port
specfact spec mock --spec api/openapi.yaml --port 9000

# Use examples mode (less strict)
specfact spec mock --spec api/openapi.yaml --examples

# Select contract from active bundle (interactive)
specfact spec mock --bundle legacy-api

# Use specific bundle (non-interactive, uses first contract)
specfact spec mock --bundle legacy-api --no-interactive
```

**CLI-First Pattern**: Uses active plan as default, or specify `--bundle`. Interactive selection when multiple contracts available.

**Features:**

- Serves API endpoints based on specification
- Validates requests against spec
- Returns example responses
- Press Ctrl+C to stop

**Common locations for auto-detection:**

- `openapi.yaml`, `openapi.yml`, `openapi.json`
- `asyncapi.yaml`, `asyncapi.yml`, `asyncapi.json`
- `api/openapi.yaml`
- `specs/openapi.yaml`

**Integration:**

The `spec` commands are automatically integrated into:

- `import from-code` - Auto-validates OpenAPI/AsyncAPI specs after import
- `enforce sdd` - Validates API specs during SDD enforcement
- `sync bridge` and `sync repository` - Auto-validates specs after sync

See [Specmatic Integration Guide](../guides/specmatic-integration.md) for detailed documentation.

---

---

### `sdd constitution` - Manage Project Constitutions (Spec-Kit Compatibility)

**Note**: Constitution management commands are part of the `sdd` (Spec-Driven Development) command group. The `specfact bridge` command group has been removed in v0.22.0 as part of the bridge adapter refactoring. Bridge adapters are now internal connectors accessed via `specfact sync bridge --adapter <adapter-name>`, not user-facing commands.

Manage project constitutions for Spec-Kit format compatibility. Auto-generate bootstrap templates from repository analysis.

**Note**: These commands are for **Spec-Kit format compatibility** only. SpecFact itself uses modular project bundles (`.specfact/projects/<bundle-name>/`) and protocols (`.specfact/protocols/*.protocol.yaml`) for internal operations. Constitutions are only needed when:

- Syncing with Spec-Kit artifacts (`specfact sync bridge --adapter speckit`)

- Working in Spec-Kit format (using `/speckit.*` commands)

- Migrating from Spec-Kit to SpecFact format

If you're using SpecFact standalone (without Spec-Kit), you don't need constitutions - use `specfact plan` commands instead.

**⚠️ Breaking Change**: The `specfact bridge constitution` command has been moved to `specfact sdd constitution` as part of the bridge adapter refactoring. Please update your scripts and workflows.

##### `sdd constitution bootstrap`

Generate bootstrap constitution from repository analysis:

```bash
specfact sdd constitution bootstrap [OPTIONS]
```

**Options:**

- `--repo PATH` - Repository path (default: current directory)
- `--out PATH` - Output path for constitution (default: `.specify/memory/constitution.md`)
- `--overwrite` - Overwrite existing constitution if it exists

**Example:**

```bash
# Generate bootstrap constitution
specfact sdd constitution bootstrap --repo .

# Generate with custom output path
specfact sdd constitution bootstrap --repo . --out custom-constitution.md

# Overwrite existing constitution
specfact sdd constitution bootstrap --repo . --overwrite
```

**What it does:**

- Analyzes repository context (README.md, pyproject.toml, .cursor/rules/, docs/rules/)
- Extracts project metadata (name, description, technology stack)
- Extracts development principles from rule files
- Generates bootstrap constitution template with:
  - Project name and description
  - Core principles (extracted from repository)
  - Development workflow guidelines
  - Quality standards
  - Governance rules
- Creates constitution at `.specify/memory/constitution.md` (Spec-Kit convention)

**When to use:**

- **Spec-Kit sync operations**: Required before `specfact sync bridge --adapter speckit` (bidirectional sync)
- **Spec-Kit format projects**: When working with Spec-Kit artifacts (using `/speckit.*` commands)
- **After brownfield import (if syncing to Spec-Kit)**: Run `specfact import from-code` → Suggested automatically if Spec-Kit sync is planned
- **Manual setup**: Generate constitution for new Spec-Kit projects

**Note**: If you're using SpecFact standalone (without Spec-Kit), you don't need constitutions. Use `specfact plan` commands instead for plan management.

**Integration:**

- **Auto-suggested** during `specfact import from-code` (brownfield imports)
- **Auto-detected** during `specfact sync bridge --adapter speckit` (if constitution is minimal)

---

##### `sdd constitution enrich`

Auto-enrich existing constitution with repository context (Spec-Kit format):

```bash
specfact sdd constitution enrich [OPTIONS]
```

**Options:**

- `--repo PATH` - Repository path (default: current directory)
- `--constitution PATH` - Path to constitution file (default: `.specify/memory/constitution.md`)

**Example:**

```bash
# Enrich existing constitution
specfact sdd constitution enrich --repo .

# Enrich specific constitution file
specfact sdd constitution enrich --repo . --constitution custom-constitution.md
```

**What it does:**

- Analyzes repository context (same as bootstrap)
- Fills remaining placeholders in existing constitution
- Adds additional principles extracted from repository
- Updates workflow and quality standards sections

**When to use:**

- Constitution has placeholders that need filling
- Repository context has changed (new rules, updated README)
- Manual constitution needs enrichment with repository details

---

##### `sdd constitution validate`

Validate constitution completeness (Spec-Kit format):

```bash
specfact sdd constitution validate [OPTIONS]
```

**Options:**

- `--constitution PATH` - Path to constitution file (default: `.specify/memory/constitution.md`)

**Example:**

```bash
# Validate default constitution
specfact sdd constitution validate

# Validate specific constitution file
specfact sdd constitution validate --constitution custom-constitution.md
```

**What it checks:**

- Constitution exists and is not empty
- No unresolved placeholders remain
- Has "Core Principles" section
- Has at least one numbered principle
- Has "Governance" section
- Has version and ratification date

**Output:**

- ✅ Valid: Constitution is complete and ready for use
- ❌ Invalid: Lists specific issues found (placeholders, missing sections, etc.)

**When to use:**

- Before syncing with Spec-Kit (`specfact sync bridge --adapter speckit` requires valid constitution)
- After manual edits to verify completeness
- In CI/CD pipelines to ensure constitution quality

---

---

---

**Note**: The `specfact constitution` command has been moved to `specfact sdd constitution`. See the [`sdd constitution`](#sdd-constitution---manage-project-constitutions) section above for complete documentation.

**Migration**: Replace `specfact constitution <command>` or `specfact bridge constitution <command>` with `specfact sdd constitution <command>`.

**Example Migration:**

- `specfact constitution bootstrap` → `specfact sdd constitution bootstrap`
- `specfact bridge constitution bootstrap` → `specfact sdd constitution bootstrap`
- `specfact constitution enrich` → `specfact sdd constitution enrich`
- `specfact bridge constitution enrich` → `specfact sdd constitution enrich`
- `specfact constitution validate` → `specfact sdd constitution validate`
- `specfact bridge constitution validate` → `specfact sdd constitution validate`

---

### `migrate` - Migration Helpers

Helper commands for migrating legacy artifacts and cleaning up deprecated structures.

#### `migrate cleanup-legacy`

Remove empty legacy top-level directories (Phase 8.5 cleanup).

```bash
specfact migrate cleanup-legacy [OPTIONS]
```

**Purpose:**

Removes legacy directories that are no longer created by newer SpecFact versions:

- `.specfact/plans/` (deprecated: no monolithic bundles, active bundle config moved to `config.yaml`)
- `.specfact/contracts/` (now bundle-specific: `.specfact/projects/<bundle-name>/contracts/`)
- `.specfact/protocols/` (now bundle-specific: `.specfact/projects/<bundle-name>/protocols/`)

**Options:**

- `--repo PATH` - Path to repository (default: `.`)
- `--dry-run` - Show what would be removed without actually removing
- `--force` - Remove directories even if they contain files (default: only removes empty directories)

**Examples:**

```bash
# Preview what would be removed
specfact migrate cleanup-legacy --dry-run

# Remove empty legacy directories
specfact migrate cleanup-legacy

# Force removal even if directories contain files
specfact migrate cleanup-legacy --force
```

**Safety:**

By default, the command only removes **empty** directories. Use `--force` to remove directories containing files (use with caution).

---

#### `migrate to-contracts`

Migrate legacy bundles to contract-centric structure.

```bash
specfact migrate to-contracts [BUNDLE] [OPTIONS]
```

**Purpose:**

Converts legacy plan bundles to the new contract-centric structure, extracting OpenAPI contracts from verbose acceptance criteria and validating with Specmatic.

**Arguments:**

- `BUNDLE` - Project bundle name. Default: active plan from `specfact plan select`

**Options:**

- `--repo PATH` - Path to repository (default: `.`)
- `--extract-openapi/--no-extract-openapi` - Extract OpenAPI contracts from verbose acceptance criteria (default: enabled)
- `--validate-with-specmatic/--no-validate-with-specmatic` - Validate generated contracts with Specmatic (default: enabled)
- `--dry-run` - Preview changes without writing
- `--no-interactive` - Non-interactive mode

**Examples:**

```bash
# Migrate bundle to contract-centric structure
specfact migrate to-contracts legacy-api

# Preview migration without writing
specfact migrate to-contracts legacy-api --dry-run

# Skip OpenAPI extraction
specfact migrate to-contracts legacy-api --no-extract-openapi
```

**What it does:**

1. Scans acceptance criteria for API-related patterns
2. Extracts OpenAPI contract definitions
3. Creates contract files in bundle-specific location
4. Validates contracts with Specmatic (if available)
5. Updates bundle manifest with contract references

---

#### `migrate artifacts`

Migrate artifacts between bundle versions or locations.

```bash
specfact migrate artifacts [BUNDLE] [OPTIONS]
```

**Purpose:**

Migrates artifacts (reports, contracts, SDDs) from legacy locations to the current bundle-specific structure.

**Arguments:**

- `BUNDLE` - Project bundle name. If not specified, migrates artifacts for all bundles found in `.specfact/projects/`

**Options:**

- `--repo PATH` - Path to repository (default: `.`)
- `--dry-run` - Show what would be migrated without actually migrating
- `--backup/--no-backup` - Create backups of original files (default: enabled)

**Examples:**

```bash
# Migrate artifacts for specific bundle
specfact migrate artifacts legacy-api

# Migrate artifacts for all bundles
specfact migrate artifacts

# Preview migration
specfact migrate artifacts legacy-api --dry-run

# Skip backups (faster, but no rollback)
specfact migrate artifacts legacy-api --no-backup
```

**What it migrates:**

- Reports from legacy locations to `.specfact/projects/<bundle>/reports/`
- Contracts from root-level to bundle-specific locations
- SDD manifests from legacy paths to bundle-specific paths

---

### `sdd` - SDD Manifest Utilities

Utilities for working with SDD (Software Design Document) manifests.

#### `sdd list`

List all SDD manifests in the repository.

```bash
specfact sdd list [OPTIONS]
```

**Purpose:**

Shows all SDD manifests found in the repository, including:

- Bundle-specific locations (`.specfact/projects/<bundle-name>/sdd.yaml`, Phase 8.5)
- Legacy multi-SDD layout (`.specfact/sdd/*.yaml`)
- Legacy single-SDD layout (`.specfact/sdd.yaml`)

**Options:**

- `--repo PATH` - Path to repository (default: `.`)

**Examples:**

```bash
# List all SDD manifests
specfact sdd list

# List SDDs in specific repository
specfact sdd list --repo /path/to/repo
```

**Output:**

Displays a table with:

- **Path**: Location of the SDD manifest
- **Bundle**: Associated bundle name (if applicable)
- **Version**: SDD schema version
- **Features**: Number of features defined

**Use Cases:**

- Discover existing SDD manifests in a repository
- Verify SDD locations after migration
- Debug SDD-related issues

---

### `implement` - Removed Task Execution

> **⚠️ REMOVED in v0.22.0**: The `implement` command group has been removed. Per SPECFACT_0x_TO_1x_BRIDGE_PLAN.md, SpecFact CLI does not create plan → feature → task (that's the job for spec-kit, openspec, etc.). We complement those SDD tools to enforce tests and quality. Use the AI IDE bridge commands (`specfact generate fix-prompt`, `specfact generate test-prompt`, etc.) instead.

#### `implement tasks` (Removed)

Direct task execution was removed in v0.22.0. Use AI IDE bridge workflows instead.

```bash
# DEPRECATED - Do not use for new projects
specfact implement tasks [OPTIONS]
```

**Migration Guide:**

Replace `implement tasks` with the new AI IDE bridge workflow:

| Old Command | New Workflow |
|-------------|--------------|
| `specfact implement tasks` | 1. `specfact generate fix-prompt GAP-ID` |
| | 2. Copy prompt to AI IDE |
| | 3. AI IDE provides the implementation |
| | 4. `specfact enforce sdd` to validate |

**Why Deprecated:**

- AI IDE integration provides better context awareness
- Human-in-the-loop validation before code changes
- Works with any AI IDE (Cursor, Copilot, Claude, etc.)
- More reliable and controllable than direct code generation

**Recommended Replacements:**

- **Fix gaps**: `specfact generate fix-prompt`
- **Add tests**: `specfact generate test-prompt`
- **Add contracts**: `specfact generate contracts-prompt`

> **⚠️ REMOVED in v0.22.0**: The `specfact generate tasks` command has been removed. Per SPECFACT_0x_TO_1x_BRIDGE_PLAN.md, SpecFact CLI does not create plan → feature → task (that's the job for spec-kit, openspec, etc.). We complement those SDD tools to enforce tests and quality.

**See**: [Migration Guide (0.16 to 0.19)](../guides/migration-0.16-to-0.19.md) for detailed migration instructions.

---

### `init` - Bootstrap and Module Lifecycle Management

Bootstrap SpecFact local state and manage enabled/disabled command modules.

```bash
specfact init [OPTIONS]
```

**Common options:**

- `--repo PATH` - Repository path (default: current directory)
- `--list-modules` - Show discovered modules with effective enabled/disabled state and exit
- `--enable-module TEXT` - Enable module by id (repeatable)
- `--disable-module TEXT` - Disable module by id (repeatable)
- `--force` - Override dependency guards; cascades dependency updates

**Interactive behavior:**

- Default mode is auto-detected from terminal + CI environment.
- In interactive terminals, passing `--enable-module` or `--disable-module` without ids opens an arrow-key selector.
- In non-interactive mode, module ids are required (for example in CI/CD).

**Dependency-aware behavior:**

- Safe disable blocks disabling a module that is required by other enabled modules.
- Safe enable blocks enabling a module when required dependencies are disabled.
- `--force` performs dependency-aware cascading:
  - disable cascades to enabled dependents
  - enable cascades to required dependencies

**Examples:**

```bash
# Bootstrap only (no IDE prompt/template copy)
specfact init

# List lifecycle state
specfact init --list-modules

# Interactive selection (TTY)
specfact init --enable-module
specfact init --disable-module

# Non-interactive explicit ids
specfact --no-interactive init --enable-module backlog
specfact --no-interactive init --disable-module upgrade

# Force dependency cascade
specfact init --enable-module sync --force
specfact init --disable-module plan --force
```

**What it does:**

1. Initializes/updates user-level registry state under `~/.specfact/registry/`.
2. Discovers installed modules and applies enable/disable operations.
3. Enforces module dependency and compatibility constraints.
4. Reports IDE prompt status and points to `specfact init ide` for prompt/template setup.

### `init ide` - IDE Prompt/Template Setup

Install and update prompt templates and IDE settings.

```bash
specfact init ide [OPTIONS]
```

**Options:**

- `--repo PATH` - Repository path (default: current directory)
- `--ide TEXT` - IDE type (cursor, vscode, copilot, claude, gemini, qwen, opencode, windsurf, kilocode, auggie, roo, codebuddy, amp, q, auto)
- `--force` - Overwrite existing files
- `--install-deps` - Install contract-enhancement dependencies (`beartype`, `icontract`, `crosshair-tool`, `pytest`)

**Behavior:**

- In interactive terminals, `specfact init ide` without `--ide` opens an arrow-key IDE selector.
- In non-interactive mode, IDE auto-detection is used unless `--ide` is explicitly provided.
- Prompt templates are copied to IDE-specific root-level locations (`.github/prompts`, `.cursor/commands`, etc.).

**Examples:**

```bash
# Interactive IDE selection
specfact init ide

# Explicit IDE
specfact init ide --ide cursor
specfact init ide --ide vscode --force

# Optional dependency installation
specfact init ide --install-deps
```

**IDE-Specific Locations:**

| IDE | Directory | Format |
|-----|-----------|--------|
| Cursor | `.cursor/commands/` | Markdown |
| VS Code / Copilot | `.github/prompts/` | `.prompt.md` |
| Claude Code | `.claude/commands/` | Markdown |
| Gemini | `.gemini/commands/` | TOML |
| Qwen | `.qwen/commands/` | TOML |
| And more... | See [IDE Integration Guide](../guides/ide-integration.md) | Markdown |

**See [IDE Integration Guide](../guides/ide-integration.md)** for detailed setup instructions and all supported IDEs.

---

### `upgrade` - Check for and Install CLI Updates

Check for and install SpecFact CLI updates from PyPI.

```bash
specfact upgrade [OPTIONS]
```

**Options:**

- `--check-only` - Only check for updates, don't install
- `--yes`, `-y` - Skip confirmation prompt and install immediately

**Examples:**

```bash
# Check for updates only
specfact upgrade --check-only

# Check and install (with confirmation)
specfact upgrade

# Check and install without confirmation
specfact upgrade --yes
```

**What it does:**

1. Checks PyPI for the latest version
2. Compares with current installed version
3. Detects installation method (pip, pipx, or uvx)
4. Optionally installs the update using the appropriate method

**Installation Method Detection:**

The command automatically detects how SpecFact CLI was installed:

- **pip**: Uses `pip install --upgrade specfact-cli`
- **pipx**: Uses `pipx upgrade specfact-cli`
- **uvx**: Informs user that uvx automatically uses latest version (no update needed)

**Update Types:**

- **Major updates** (🔴): May contain breaking changes - review release notes before upgrading
- **Minor/Patch updates** (🟡): Backward compatible improvements and bug fixes

**Note**: The upgrade command respects the same rate limiting as startup checks (checks are cached for 24 hours in `~/.specfact/metadata.json`).

---

## IDE Integration (Slash Commands)

Slash commands provide an intuitive interface for IDE integration (VS Code, Cursor, GitHub Copilot, etc.).

### Available Slash Commands

**Core Workflow Commands** (numbered for workflow ordering):

1. `/specfact.01-import [args]` - Import codebase into plan bundle (replaces `specfact-import-from-code`)
2. `/specfact.02-plan [args]` - Plan management: init, add-feature, add-story, update-idea, update-feature, update-story (replaces `specfact-plan-init`, `specfact-plan-add-feature`, `specfact-plan-add-story`, `specfact-plan-update-idea`, `specfact-plan-update-feature`)
3. `/specfact.03-review [args]` - Review plan and promote (replaces `specfact-plan-review`, `specfact-plan-promote`)
4. `/specfact.04-sdd [args]` - Create SDD manifest (new, based on `plan harden`)
5. `/specfact.05-enforce [args]` - SDD enforcement (replaces `specfact-enforce`)
6. `/specfact.06-sync [args]` - Sync operations (replaces `specfact-sync`)
7. `/specfact.07-contracts [args]` - Contract enhancement workflow: analyze → generate prompts → apply contracts sequentially

**Advanced Commands** (no numbering):

- `/specfact.compare [args]` - Compare plans (replaces `specfact-plan-compare`)
- `/specfact.validate [args]` - Validation suite (replaces `specfact-repro`)
- `/specfact.generate-contracts-prompt [args]` - Generate AI IDE prompt for adding contracts (see `generate contracts-prompt`)

### Setup

```bash
# Initialize IDE integration (one-time setup)
specfact init ide --ide cursor

# Or auto-detect IDE
specfact init ide

# Initialize and install required packages for contract enhancement
specfact init ide --install-deps

# Initialize for specific IDE and install dependencies
specfact init ide --ide cursor --install-deps
```

### Usage

After initialization, use slash commands directly in your IDE's AI chat:

```bash
# In IDE chat (Cursor, VS Code, Copilot, etc.)
# Core workflow (numbered for natural progression)
/specfact.01-import legacy-api --repo .
/specfact.02-plan init legacy-api
/specfact.02-plan add-feature --bundle legacy-api --key FEATURE-001 --title "User Auth"
/specfact.03-review legacy-api
/specfact.04-sdd legacy-api
/specfact.05-enforce legacy-api
/specfact.06-sync --repo . --adapter speckit
/specfact.07-contracts legacy-api --apply all-contracts  # Analyze, generate prompts, apply contracts sequentially

# Advanced commands
/specfact.compare --bundle legacy-api
/specfact.validate --repo .
```

**How it works:**

Slash commands are **prompt templates** (markdown files) that are copied to IDE-specific locations by `specfact init ide`. The IDE automatically discovers and registers them as slash commands.

**See [IDE Integration Guide](../guides/ide-integration.md)** for detailed setup instructions and supported IDEs.

---

## Environment Variables

- `SPECFACT_CONFIG` - Path to config file (default: `.specfact/config.yaml`)
- `SPECFACT_VERBOSE` - Enable verbose output (0/1)
- `SPECFACT_NO_COLOR` - Disable colored output (0/1)
- `SPECFACT_MODE` - Operational mode (`cicd` or `copilot`)
- `COPILOT_API_URL` - CoPilot API endpoint (for CoPilot mode detection)

---

## Configuration File

Create `.specfact.yaml` in project root:

```yaml
version: "1.0"

# Enforcement settings
enforcement:
  preset: balanced
  custom_rules: []

# Analysis settings
analysis:
  confidence_threshold: 0.7
  include_tests: true
  exclude_patterns:
    - "**/__pycache__/**"
    - "**/node_modules/**"

# Import settings
import:
  default_branch: feat/specfact-migration
  preserve_history: true

# Repro settings
repro:
  budget: 120
  parallel: true
  fail_fast: false
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation/enforcement failed |
| 2 | Time budget exceeded |
| 3 | Configuration error |
| 4 | File not found |
| 5 | Invalid arguments |

---

## Shell Completion

SpecFact CLI supports native shell completion for bash, zsh, and fish **without requiring any extensions**. Completion works automatically once installed.

### Quick Install

Use Typer's built-in completion commands:

```bash
# Auto-detect shell and install (recommended)
specfact --install-completion

# Explicitly specify shell
specfact --install-completion bash   # or zsh, fish
```

### Show Completion Script

To view the completion script without installing:

```bash
# Auto-detect shell
specfact --show-completion

# Explicitly specify shell
specfact --show-completion bash
```

### Manual Installation

You can also manually add completion to your shell config:

#### Bash

```bash
# Add to ~/.bashrc
eval "$(_SPECFACT_COMPLETE=bash_source specfact)"
```

#### Zsh

```bash
# Add to ~/.zshrc
eval "$(_SPECFACT_COMPLETE=zsh_source specfact)"
```

#### Fish

```fish
# Add to ~/.config/fish/config.fish
eval (env _SPECFACT_COMPLETE=fish_source specfact)
```

### PowerShell

PowerShell completion requires the `click-pwsh` extension:

```powershell
pip install click-pwsh
python -m click_pwsh install specfact
```

### Ubuntu/Debian Notes

On Ubuntu and Debian systems, `/bin/sh` points to `dash` instead of `bash`. SpecFact CLI automatically normalizes shell detection to use `bash` for completion, so auto-detection works correctly even on these systems.

If you encounter "Shell sh not supported" errors, explicitly specify the shell:

```bash
specfact --install-completion bash
```

---

## Related Documentation

- [Getting Started](../getting-started/README.md) - Installation and first steps
- [First Steps](../getting-started/first-steps.md) - Step-by-step first commands
- [Use Cases](../guides/use-cases.md) - Real-world scenarios
- [Workflows](../guides/workflows.md) - Common daily workflows
- [IDE Integration](../guides/ide-integration.md) - Set up slash commands
- [Troubleshooting](../guides/troubleshooting.md) - Common issues and solutions
- [Architecture](architecture.md) - Technical design and principles
- [Quick Examples](../examples/quick-examples.md) - Code snippets
