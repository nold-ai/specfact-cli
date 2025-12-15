# Command Reference

Complete reference for all SpecFact CLI commands.

## Quick Reference

### Most Common Commands

```bash
# PRIMARY: Import from existing code (brownfield modernization)
specfact import from-code --bundle legacy-api --repo .

# SECONDARY: Import from external tools (Spec-Kit, Linear, Jira, etc.)
specfact import from-bridge --repo . --adapter speckit --write

# Initialize plan (alternative: greenfield workflow)
specfact plan init --bundle legacy-api --interactive

# Compare plans
specfact plan compare --bundle legacy-api

# Sync with external tools (bidirectional) - Secondary use case
specfact sync bridge --adapter speckit --bundle legacy-api --bidirectional --watch

# Validate everything
specfact repro --verbose
```

### Global Flags

- `--input-format {yaml,json}` - Override default structured input detection for CLI commands (defaults to YAML)
- `--output-format {yaml,json}` - Control how plan bundles and reports are written (JSON is ideal for CI/copilot automations)
- `--interactive/--no-interactive` - Force prompt behavior (overrides auto-detection from CI/CD vs Copilot environments)

### Commands by Workflow

**Import & Analysis:**

- `import from-code` ⭐ **PRIMARY** - Analyze existing codebase (brownfield modernization)
- `import from-bridge` - Import from external tools via bridge architecture (Spec-Kit, Linear, Jira, etc.)

**Plan Management:**

- `plan init --bundle <bundle-name>` - Initialize new project bundle
- `plan add-feature --bundle <bundle-name>` - Add feature to bundle
- `plan add-story --bundle <bundle-name>` - Add story to feature
- `plan update-feature --bundle <bundle-name>` - Update existing feature metadata
- `plan review --bundle <bundle-name>` - Review plan bundle to resolve ambiguities
- `plan select` - Select active plan from available bundles
- `plan upgrade` - Upgrade plan bundles to latest schema version
- `plan compare` - Compare plans (detect drift)

**Project Bundle Management:**

- `project export --bundle <bundle-name> --persona <persona>` - Export persona-specific Markdown artifacts
- `project import --bundle <bundle-name> --persona <persona> --source <file>` - Import persona edits from Markdown
- `project version check --bundle <bundle-name>` - Recommend version bump (major/minor/patch/none)
- `project version bump --bundle <bundle-name> --type <major|minor|patch>` - Apply SemVer bump and record history
- `project version set --bundle <bundle-name> --version <semver>` - Set explicit project version and record history
- CI template support: the provided GitHub Action template now runs a non-blocking `project version check` step after contract validation.

**Enforcement:**

- `enforce stage` - Configure quality gates
- `repro` - Run validation suite

**Synchronization:**

- `sync bridge` - Sync with external tools via bridge architecture (Spec-Kit, Linear, Jira, etc.)
- `sync repository` - Sync code changes

**API Specification Management:**

- `spec validate` - Validate OpenAPI/AsyncAPI specifications with Specmatic
- `spec backward-compat` - Check backward compatibility between spec versions
- `spec generate-tests` - Generate contract tests from specifications
- `spec mock` - Launch mock server for development

**Constitution Management (Spec-Kit Compatibility):**

- `bridge constitution bootstrap` - Generate bootstrap constitution from repository analysis (for Spec-Kit format)
- `bridge constitution enrich` - Auto-enrich existing constitution with repository context (for Spec-Kit format)
- `bridge constitution validate` - Validate constitution completeness (for Spec-Kit format)

**Note**: The `bridge constitution` commands are for **Spec-Kit compatibility** only. SpecFact itself uses modular project bundles (`.specfact/projects/<bundle-name>/`) and protocols (`.specfact/protocols/*.protocol.yaml`) for internal operations. Constitutions are only needed when syncing with Spec-Kit artifacts or working in Spec-Kit format.

**⚠️ Deprecation Notice**: The old `specfact constitution` command is deprecated and will be removed in a future version. Please use `specfact bridge constitution` instead.

**Setup:**

- `init` - Initialize IDE integration

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

The CLI displays an ASCII art banner by default for brand recognition and visual appeal. The banner shows:

- When executing any command (unless `--no-banner` is specified)
- With help output (`--help` or `-h`)
- With version output (`--version` or `-v`)

To suppress the banner (useful for CI/CD or automated scripts):

```bash
specfact --no-banner <command>
```

**Examples:**

```bash
# Auto-detect mode (default)
specfact import from-code --bundle legacy-api --repo .

# Force CI/CD mode
specfact --mode cicd import from-code --bundle legacy-api --repo .

# Force CoPilot mode
specfact --mode copilot import from-code --bundle legacy-api --repo .
```

## Commands

### `import` - Import from External Formats

Convert external project formats to SpecFact format.

#### `import from-bridge`

Convert external tool projects (Spec-Kit, Linear, Jira, etc.) to SpecFact format using the bridge architecture.

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

- `--adapter ADAPTER` - Adapter type: `speckit`, `generic-markdown` (default: auto-detect)

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
- `--enrichment PATH` - Path to Markdown enrichment report from LLM (applies missing features, confidence adjustments, business context)

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
specfact import from-code --bundle legacy-api \
  --repo ./my-project \
  --confidence 0.7 \
  --shadow-only \
  --report reports/analysis.md

# Partial analysis (analyze only specific subdirectory)
specfact import from-code --bundle core-module \
  --repo ./my-project \
  --entry-point src/core \
  --confidence 0.7

# Multi-project codebase (analyze one project at a time)
specfact import from-code --bundle api-service \
  --repo ./monorepo \
  --entry-point projects/api-service
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
- Run `specfact init` from the repository root to ensure IDE integration works correctly (templates are copied to root-level `.github/`, `.cursor/`, etc. directories)

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
specfact plan init --bundle legacy-api --interactive

# Non-interactive mode (CI/CD automation)
specfact plan init --bundle legacy-api --no-interactive

# Interactive mode with different bundle
specfact plan init --bundle feature-auth --interactive
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
specfact plan review --bundle legacy-api

# Get all findings for bulk updates (preferred for Copilot mode)
specfact plan review --bundle legacy-api --list-findings --findings-format json

# Save findings directly to file (clean JSON, no CLI banner)
specfact plan review --bundle legacy-api --list-findings --output-findings /tmp/findings.json

# Get findings as table (interactive mode)
specfact plan review --bundle legacy-api --list-findings --findings-format table

# Get questions for question-based workflow
specfact plan review --bundle legacy-api --list-questions --max-questions 5

# Save questions directly to file (clean JSON, no CLI banner)
specfact plan review --bundle legacy-api --list-questions --output-questions /tmp/questions.json

# Feed answers back (question-based workflow)
specfact plan review --bundle legacy-api --answers answers.json

# CI/CD automation
specfact plan review --bundle legacy-api --no-interactive --answers answers.json
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

- Bundle name is provided as a positional argument (e.g., `plan upgrade my-project`)
- `--all` - Upgrade all project bundles in `.specfact/projects/`
- `--dry-run` - Show what would be upgraded without making changes

**Example:**

```bash
# Preview what would be upgraded
specfact plan upgrade --dry-run

# Upgrade active plan
specfact plan upgrade

# Upgrade specific plan (bundle name as positional argument)
specfact plan upgrade my-project

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

**Note**: Upgraded plan bundles are backward compatible. Older CLI versions can still read them, but won't benefit from performance optimizations.

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

```
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

**Press Ctrl+C to stop the server**

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

```
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

- `--verbose` - Show detailed output
- `--fix` - Apply auto-fixes where available (Semgrep auto-fixes)
- `--fail-fast` - Stop on first failure
- `--out PATH` - Output report path (default: bundle-specific `.specfact/projects/<bundle-name>/reports/enforcement/report-<timestamp>.yaml`, Phase 8.5, or global `.specfact/reports/enforcement/` if no bundle context)

**Advanced Options** (hidden by default, use `--help-advanced` or `-ha` to view):

- `--budget INT` - Time budget in seconds (default: 120)

**Example:**

```bash
# Standard validation
specfact repro --verbose --budget 120

# Apply auto-fixes for violations
specfact repro --fix --budget 120

# Stop on first failure
specfact repro --fail-fast
```

**What it runs:**

1. **Lint checks** - ruff, semgrep async rules
2. **Type checking** - mypy/basedpyright
3. **Contract exploration** - CrossHair
4. **Property tests** - Hypothesis
5. **Smoke tests** - Event loop lag, orphaned tasks
6. **Plan validation** - Schema compliance

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

### `sync` - Synchronize Changes

Bidirectional synchronization for consistent change management.

#### `sync bridge`

Sync changes between external tool artifacts (Spec-Kit, Linear, Jira, etc.) and SpecFact using the bridge architecture:

```bash
specfact sync bridge [OPTIONS]
```

**Options:**

- `--repo PATH` - Path to repository (default: `.`)
- `--adapter ADAPTER` - Adapter type: `speckit`, `generic-markdown` (default: auto-detect)
- `--bundle BUNDLE_NAME` - Project bundle name for SpecFact → tool conversion (default: auto-detect)
- `--bidirectional` - Enable bidirectional sync (default: one-way import)
- `--overwrite` - Overwrite existing tool artifacts (delete all existing before sync)
- `--watch` - Watch mode for continuous sync (monitors file changes in real-time)
- `--interval INT` - Watch interval in seconds (default: 5, minimum: 1)
- `--ensure-compliance` - Validate and auto-enrich plan bundle for tool compliance before sync

**Watch Mode Features:**

- **Hash-based change detection**: Only processes files that actually changed (SHA256 hash verification)
- **Real-time monitoring**: Automatically detects file changes in tool artifacts, SpecFact bundles, and repository code
- **Dependency tracking**: Tracks file dependencies for incremental processing
- **Debouncing**: Prevents rapid file change events (500ms debounce interval)
- **Change type detection**: Automatically detects whether changes are in tool artifacts, SpecFact bundles, or code
- **LZ4 cache compression**: Faster cache I/O when LZ4 is available (optional)
- **Graceful shutdown**: Press Ctrl+C to stop watch mode cleanly
- **Resource efficient**: Minimal CPU/memory usage

**Example:**

```bash
# One-time bidirectional sync with Spec-Kit
specfact sync bridge --adapter speckit --repo . --bundle my-project --bidirectional

# Auto-detect adapter and bundle
specfact sync bridge --repo . --bidirectional

# Overwrite tool artifacts with SpecFact bundle
specfact sync bridge --adapter speckit --repo . --bundle my-project --bidirectional --overwrite

# Continuous watch mode
specfact sync bridge --adapter speckit --repo . --bundle my-project --bidirectional --watch --interval 5
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

### `bridge` - Bridge Adapters for External Tool Integration

Bridge adapters for external tool integration (Spec-Kit, Linear, Jira, etc.). These commands enable bidirectional sync and format conversion between SpecFact and external tools.

#### `bridge constitution` - Manage Project Constitutions

Manage project constitutions for Spec-Kit format compatibility. Auto-generate bootstrap templates from repository analysis.

**Note**: These commands are for **Spec-Kit format compatibility** only. SpecFact itself uses modular project bundles (`.specfact/projects/<bundle-name>/`) and protocols (`.specfact/protocols/*.protocol.yaml`) for internal operations. Constitutions are only needed when:

- Syncing with Spec-Kit artifacts (`specfact sync bridge --adapter speckit`)

- Working in Spec-Kit format (using `/speckit.*` commands)

- Migrating from Spec-Kit to SpecFact format

If you're using SpecFact standalone (without Spec-Kit), you don't need constitutions - use `specfact plan` commands instead.

**Deprecation Notice**: The old `specfact constitution` command is deprecated and will be removed in a future version. Please use `specfact bridge constitution` instead.

##### `bridge constitution bootstrap`

Generate bootstrap constitution from repository analysis:

```bash
specfact bridge constitution bootstrap [OPTIONS]
```

**Options:**

- `--repo PATH` - Repository path (default: current directory)
- `--out PATH` - Output path for constitution (default: `.specify/memory/constitution.md`)
- `--overwrite` - Overwrite existing constitution if it exists

**Example:**

```bash
# Generate bootstrap constitution
specfact bridge constitution bootstrap --repo .

# Generate with custom output path
specfact bridge constitution bootstrap --repo . --out custom-constitution.md

# Overwrite existing constitution
specfact bridge constitution bootstrap --repo . --overwrite
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

##### `bridge constitution enrich`

Auto-enrich existing constitution with repository context (Spec-Kit format):

```bash
specfact bridge constitution enrich [OPTIONS]
```

**Options:**

- `--repo PATH` - Repository path (default: current directory)
- `--constitution PATH` - Path to constitution file (default: `.specify/memory/constitution.md`)

**Example:**

```bash
# Enrich existing constitution
specfact bridge constitution enrich --repo .

# Enrich specific constitution file
specfact bridge constitution enrich --repo . --constitution custom-constitution.md
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

##### `bridge constitution validate`

Validate constitution completeness (Spec-Kit format):

```bash
specfact bridge constitution validate [OPTIONS]
```

**Options:**

- `--constitution PATH` - Path to constitution file (default: `.specify/memory/constitution.md`)

**Example:**

```bash
# Validate default constitution
specfact bridge constitution validate

# Validate specific constitution file
specfact bridge constitution validate --constitution custom-constitution.md
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

**Note**: The old `specfact constitution` command has been moved to `specfact bridge constitution`. See the [`bridge constitution`](#bridge-constitution---manage-project-constitutions) section above for complete documentation. The old command path is deprecated and will be removed in a future version.

**Migration**: Replace `specfact constitution <command>` with `specfact bridge constitution <command>`.

**Example Migration:**

- `specfact constitution bootstrap` → `specfact bridge constitution bootstrap`
- `specfact constitution enrich` → `specfact bridge constitution enrich`
- `specfact constitution validate` → `specfact bridge constitution validate`

---

### `init` - Initialize IDE Integration

Set up SpecFact CLI for IDE integration by copying prompt templates to IDE-specific locations.

```bash
specfact init [OPTIONS]
```

**Options:**

- `--repo PATH` - Repository path (default: current directory)
- `--force` - Overwrite existing files
- `--install-deps` - Install required packages for contract enhancement (beartype, icontract, crosshair-tool, pytest) via pip

**Advanced Options** (hidden by default, use `--help-advanced` or `-ha` to view):

- `--ide TEXT` - IDE type (auto, cursor, vscode, copilot, claude, gemini, qwen, opencode, windsurf, kilocode, auggie, roo, codebuddy, amp, q) (default: auto)

**Examples:**

```bash
# Auto-detect IDE
specfact init

# Specify IDE explicitly
specfact init --ide cursor
specfact init --ide vscode
specfact init --ide copilot

# Force overwrite existing files
specfact init --ide cursor --force

# Install required packages for contract enhancement
specfact init --install-deps

# Initialize IDE integration and install dependencies
specfact init --ide cursor --install-deps
```

**What it does:**

1. Detects your IDE (or uses `--ide` flag)
2. Copies prompt templates from `resources/prompts/` to IDE-specific location **at the repository root level**
3. Creates/updates VS Code settings.json if needed (for VS Code/Copilot)
4. Makes slash commands available in your IDE
5. Optionally installs required packages for contract enhancement (if `--install-deps` is provided):
   - `beartype>=0.22.4` - Runtime type checking
   - `icontract>=2.7.1` - Design-by-contract decorators
   - `crosshair-tool>=0.0.97` - Contract exploration
   - `pytest>=8.4.2` - Testing framework

**Important:** Templates are always copied to the repository root level (where `.github/`, `.cursor/`, etc. directories must reside for IDE recognition). The `--repo` parameter specifies the repository root path. For multi-project codebases, run `specfact init` from the repository root to ensure IDE integration works correctly.

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
specfact init --ide cursor

# Or auto-detect IDE
specfact init

# Initialize and install required packages for contract enhancement
specfact init --install-deps

# Initialize for specific IDE and install dependencies
specfact init --ide cursor --install-deps
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

Slash commands are **prompt templates** (markdown files) that are copied to IDE-specific locations by `specfact init`. The IDE automatically discovers and registers them as slash commands.

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
