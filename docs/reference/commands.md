# Command Reference

Complete reference for all SpecFact CLI commands.

## Global Options

```bash
specfact [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**

- `--version` - Show version and exit
- `--help` - Show help message and exit
- `--verbose` - Enable verbose output
- `--quiet` - Suppress non-error output
- `--mode {cicd|copilot}` - Operational mode (default: auto-detect)

**Mode Selection:**

- `cicd` - CI/CD automation mode (fast, deterministic)
- `copilot` - CoPilot-enabled mode (interactive, enhanced prompts)
- Auto-detection: Checks CoPilot API availability and IDE integration

**Examples:**

```bash
# Auto-detect mode (default)
specfact import from-code --repo .

# Force CI/CD mode
specfact --mode cicd import from-code --repo .

# Force CoPilot mode
specfact --mode copilot import from-code --repo .
```

## Commands

### `import` - Import from External Formats

Convert external project formats to SpecFact format.

#### `import from-spec-kit`

Convert GitHub Spec-Kit projects:

```bash
specfact import from-spec-kit [OPTIONS]
```

**Options:**

- `--repo PATH` - Path to Spec-Kit repository (required)
- `--dry-run` - Preview without writing files
- `--write` - Write converted files to repository
- `--out-branch NAME` - Git branch for migration (default: `feat/specfact-migration`)
- `--report PATH` - Write migration report to file

**Example:**

```bash
specfact import from-spec-kit \
  --repo ./my-speckit-project \
  --write \
  --out-branch feat/specfact-migration \
  --report migration-report.md
```

**What it does:**

- Detects Spec-Kit structure (`.specify/` directory with markdown artifacts in `specs/` folders)
- Parses Spec-Kit artifacts (`specs/[###-feature-name]/spec.md`, `plan.md`, `tasks.md`, `.specify/memory/constitution.md`)
- Converts Spec-Kit features/stories to Pydantic models with contracts
- Generates `.specfact/protocols/workflow.protocol.yaml` (if FSM detected)
- Creates `.specfact/plans/main.bundle.yaml` with features and stories
- Adds Semgrep async anti-pattern rules (if async patterns detected)
- Generates GitHub Action workflow for PR validation (optional)

---

#### `import from-code`

Import plan bundle from existing codebase (one-way import) using **AI-first approach** (CoPilot mode) or **AST-based fallback** (CI/CD mode).

```bash
specfact import from-code [OPTIONS]
```

**Options:**

- `--repo PATH` - Path to repository to import (required)
- `--name NAME` - Custom plan name (will be sanitized for filesystem, default: "auto-derived")
- `--out PATH` - Output path for generated plan (default: `.specfact/plans/<name>-<timestamp>.bundle.yaml`)
- `--confidence FLOAT` - Minimum confidence score (0.0-1.0, default: 0.5)
- `--shadow-only` - Observe without blocking
- `--report PATH` - Write import report
- `--key-format {classname|sequential}` - Feature key format (default: `classname`)

**Note**: The `--name` option allows you to provide a meaningful name for the imported plan. The name will be automatically sanitized (lowercased, spaces/special chars removed) for filesystem persistence. If not provided, the AI will ask you interactively for a name.

**Mode Behavior:**

- **CoPilot Mode** (AI-first - Pragmatic): Uses AI IDE's native LLM (Cursor, CoPilot, etc.) for semantic understanding. The AI IDE understands the codebase semantically, then calls the SpecFact CLI for structured analysis. No separate LLM API setup needed. Multi-language support, high-quality Spec-Kit artifacts.
- **CI/CD Mode** (AST fallback): Uses Python AST for fast, deterministic analysis (Python-only). Works offline, no LLM required.

**Pragmatic Integration**:

- ✅ **No separate LLM setup** - Uses AI IDE's existing LLM
- ✅ **No additional API costs** - Leverages existing IDE infrastructure
- ✅ **Simpler architecture** - No langchain, API keys, or complex integration
- ✅ **Better developer experience** - Native IDE integration via slash commands

**Note**: The command automatically detects mode based on CoPilot API availability. Use `--mode` to override.

- `--mode {cicd|copilot}` - Operational mode (default: auto-detect)

**Example:**

```bash
specfact import from-code \
  --repo ./my-project \
  --confidence 0.7 \
  --shadow-only \
  --report reports/analysis.md
```

**What it does:**

- Builds module dependency graph
- Mines commit history for feature boundaries
- Extracts acceptance criteria from tests
- Infers API surfaces from type hints
- Detects async anti-patterns with Semgrep
- Generates plan bundle with confidence scores

---

### `plan` - Manage Development Plans

Create and manage contract-driven development plans.

#### `plan init`

Initialize a new plan bundle:

```bash
specfact plan init [OPTIONS]
```

**Options:**

- `--interactive` - Interactive wizard (recommended)
- `--template NAME` - Use template (default, minimal, full)
- `--out PATH` - Output path (default: `contracts/plans/plan.bundle.yaml`)

**Example:**

```bash
specfact plan init --interactive
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
- `--plan PATH` - Plan bundle path (default: `contracts/plans/plan.bundle.yaml`)

**Example:**

```bash
specfact plan add-feature \
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

- `--feature TEXT` - Feature key (required)
- `--key TEXT` - Story key (STORY-XXX) (required)
- `--title TEXT` - Story title (required)
- `--acceptance TEXT` - Acceptance criteria (multiple allowed)
- `--plan PATH` - Plan bundle path

**Example:**

```bash
specfact plan add-story \
  --feature FEATURE-001 \
  --key STORY-001 \
  --title "Parse Spec-Kit artifacts" \
  --acceptance "Schema validation passes"
```

#### `plan select`

Select active plan from available plan bundles:

```bash
specfact plan select [PLAN]
```

**Arguments:**

- `PLAN` - Plan name or number to select (optional, for interactive selection)

**Options:**

- None (interactive selection by default)

**Example:**

```bash
# Interactive selection (displays numbered list)
specfact plan select

# Select by number
specfact plan select 1

# Select by name
specfact plan select main.bundle.yaml
```

**What it does:**

- Lists all available plan bundles in `.specfact/plans/` with metadata (features, stories, stage, modified date)
- Displays numbered list with active plan indicator
- Updates `.specfact/plans/config.yaml` to set the active plan
- The active plan becomes the default for all plan operations

**Note**: The active plan is tracked in `.specfact/plans/config.yaml` and replaces the static `main.bundle.yaml` reference. All plan commands (`compare`, `promote`, `add-feature`, `add-story`, `sync spec-kit`) now use the active plan by default.

#### `plan compare`

Compare manual and auto-derived plans:

```bash
specfact plan compare [OPTIONS]
```

**Options:**

- `--manual PATH` - Manual plan bundle (default: active plan from `.specfact/plans/config.yaml` or `main.bundle.yaml`)
- `--auto PATH` - Auto-derived plan bundle (default: latest in `.specfact/plans/`)
- `--format TEXT` - Output format (markdown, json, yaml) (default: markdown)
- `--out PATH` - Output file (default: `.specfact/reports/comparison/report-*.md`)
- `--mode {cicd|copilot}` - Operational mode (default: auto-detect)

**Example:**

```bash
specfact plan compare \
  --manual contracts/plans/plan.bundle.yaml \
  --auto reports/brownfield-plan.yaml \
  --format markdown \
  --out reports/deviation.md
```

**Output includes:**

- Missing features (in manual but not in auto)
- Extra features (in auto but not in manual)
- Mismatched stories
- Confidence scores
- Deviation severity

---

### `enforce` - Configure Quality Gates

Set contract enforcement policies.

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

### `repro` - Reproducibility Validation

Run full validation suite for reproducibility.

```bash
specfact repro [OPTIONS]
```

**Options:**

- `--verbose` - Show detailed output
- `--budget INT` - Time budget in seconds (default: 120)
- `--fix` - Apply auto-fixes where available (Semgrep auto-fixes)
- `--fail-fast` - Stop on first failure
- `--out PATH` - Output report path (default: `.specfact/reports/enforcement/report-<timestamp>.yaml`)

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

Reports are written as YAML files to `.specfact/reports/enforcement/report-<timestamp>.yaml`. Each report includes:

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
  active_plan_path: .specfact/plans/main.bundle.yaml
  enforcement_config_path: .specfact/gates/config/enforcement.yaml
  enforcement_preset: balanced
  fix_enabled: false
  fail_fast: false
```

---

### `sync` - Synchronize Changes

Bidirectional synchronization for consistent change management.

#### `sync spec-kit`

Sync changes between Spec-Kit artifacts and SpecFact:

```bash
specfact sync spec-kit [OPTIONS]
```

**Options:**

- `--repo PATH` - Path to repository (default: `.`)
- `--bidirectional` - Enable bidirectional sync (default: one-way import)
- `--plan PATH` - Path to SpecFact plan bundle for SpecFact → Spec-Kit conversion (default: active plan from `.specfact/plans/config.yaml` or `main.bundle.yaml`)
- `--overwrite` - Overwrite existing Spec-Kit artifacts (delete all existing before sync)
- `--watch` - Watch mode for continuous sync
- `--interval INT` - Watch interval in seconds (default: 5)

**Example:**

```bash
# One-time bidirectional sync
specfact sync spec-kit --repo . --bidirectional

# Sync with auto-derived plan (from codebase)
specfact sync spec-kit --repo . --bidirectional --plan .specfact/plans/my-project-<timestamp>.bundle.yaml

# Overwrite Spec-Kit with auto-derived plan (32 features from codebase)
specfact sync spec-kit --repo . --bidirectional --plan .specfact/plans/my-project-<timestamp>.bundle.yaml --overwrite

# Continuous watch mode
specfact sync spec-kit --repo . --bidirectional --watch --interval 5
```

**What it syncs:**

- `specs/[###-feature-name]/spec.md`, `plan.md`, `tasks.md` ↔ `.specfact/plans/*.yaml`
- `.specify/memory/constitution.md` ↔ SpecFact business context
- `specs/[###-feature-name]/research.md`, `data-model.md`, `quickstart.md` ↔ SpecFact supporting artifacts
- `specs/[###-feature-name]/contracts/*.yaml` ↔ SpecFact protocol definitions
- Automatic conflict resolution with priority rules

#### `sync repository`

Sync code changes to SpecFact artifacts:

```bash
specfact sync repository [OPTIONS]
```

**Options:**

- `--repo PATH` - Path to repository (default: `.`)
- `--target PATH` - Target directory for artifacts (default: `.specfact`)
- `--watch` - Watch mode for continuous sync
- `--interval INT` - Watch interval in seconds (default: 5)
- `--mode {cicd|copilot}` - Operational mode (default: auto-detect)

**Example:**

```bash
# One-time sync
specfact sync repository --repo . --target .specfact

# Continuous watch mode
specfact sync repository --repo . --watch --interval 5
```

**What it tracks:**

- Code changes → Plan artifact updates
- Deviations from manual plans
- Feature/story extraction from code

---

### `init` - Initialize IDE Integration

Set up SpecFact CLI for IDE integration by copying prompt templates to IDE-specific locations.

```bash
specfact init [OPTIONS]
```

**Options:**

- `--ide TEXT` - IDE type (auto, cursor, vscode, copilot, claude, gemini, qwen, opencode, windsurf, kilocode, auggie, roo, codebuddy, amp, q) (default: auto)
- `--repo PATH` - Repository path (default: current directory)
- `--force` - Overwrite existing files

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
```

**What it does:**

1. Detects your IDE (or uses `--ide` flag)
2. Copies prompt templates from `resources/prompts/` to IDE-specific location
3. Creates/updates VS Code settings.json if needed (for VS Code/Copilot)
4. Makes slash commands available in your IDE

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

- `/specfact-import-from-code [args]` - Import codebase into plan bundle (one-way import)
- `/specfact-plan-init [args]` - Initialize plan bundle
- `/specfact-plan-promote [args]` - Promote plan through stages
- `/specfact-plan-compare [args]` - Compare manual vs auto plans
- `/specfact-sync [args]` - Bidirectional sync

### Setup

```bash
# Initialize IDE integration (one-time setup)
specfact init --ide cursor

# Or auto-detect IDE
specfact init
```

### Usage

After initialization, use slash commands directly in your IDE's AI chat:

```bash
# In IDE chat (Cursor, VS Code, Copilot, etc.)
/specfact-import-from-code --repo . --confidence 0.7
/specfact-plan-init --idea idea.yaml
/specfact-plan-compare --manual main.bundle.yaml --auto auto.bundle.yaml
/specfact-sync --repo . --bidirectional
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

### Bash

```bash
eval "$(_SPECFACT_COMPLETE=bash_source specfact)"
```

### Zsh

```bash
eval "$(_SPECFACT_COMPLETE=zsh_source specfact)"
```

### Fish

```bash
eval (env _SPECFACT_COMPLETE=fish_source specfact)
```

---

See [Getting Started](../getting-started/README.md) for quick examples and [Use Cases](../guides/use-cases.md) for detailed scenarios.
