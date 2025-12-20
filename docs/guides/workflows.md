# Common Workflows

Daily workflows for using SpecFact CLI effectively.

> **Primary Workflow**: Brownfield code modernization  
> **Secondary Workflow**: Spec-Kit bidirectional sync

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow. Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE. No platform to learn, no vendor lock-in.

---

## Brownfield Code Modernization ⭐ PRIMARY

Reverse engineer existing code and enforce contracts incrementally.

**Integration**: Works with VS Code, Cursor, GitHub Actions, pre-commit hooks. See [Integration Showcases](../examples/integration-showcases/) for real examples.

### Step 1: Analyze Legacy Code

```bash
# Full repository analysis
specfact import from-code --bundle legacy-api --repo .

# For large codebases, analyze specific modules:
specfact import from-code --bundle core-module --repo . --entry-point src/core
specfact import from-code --bundle api-module --repo . --entry-point src/api
```

### Step 2: Review Extracted Specs

```bash
# Review bundle to understand extracted specs
specfact plan review --bundle legacy-api

# Or get structured findings for analysis
specfact plan review --bundle legacy-api --list-findings --findings-format json
```

**Note**: Use CLI commands to interact with bundles. The bundle structure (`.specfact/projects/<bundle-name>/`) is managed by SpecFact CLI - use commands like `plan review`, `plan add-feature`, `plan update-feature` to modify bundles, not direct file editing.

### Step 3: Add Contracts Incrementally

```bash
# Start in shadow mode
specfact enforce stage --preset minimal
```

See [Brownfield Journey Guide](brownfield-journey.md) for complete workflow.

### Partial Repository Coverage

For large codebases or monorepos with multiple projects, use `--entry-point` to analyze specific subdirectories:

```bash
# Analyze individual projects in a monorepo
specfact import from-code --bundle api-service --repo . --entry-point projects/api-service
specfact import from-code --bundle web-app --repo . --entry-point projects/web-app
specfact import from-code --bundle mobile-app --repo . --entry-point projects/mobile-app

# Analyze specific modules for incremental modernization
specfact import from-code --bundle core-module --repo . --entry-point src/core
specfact import from-code --bundle integrations-module --repo . --entry-point src/integrations
```

**Benefits:**

- **Faster analysis** - Focus on specific modules for quicker feedback
- **Incremental modernization** - Modernize one module at a time
- **Multi-bundle support** - Create separate project bundles for different projects/modules
- **Better organization** - Keep bundles organized by project boundaries

**Note:** When using `--entry-point`, each analysis creates a separate project bundle. Use `specfact plan compare` to compare different bundles.

---

## Bidirectional Sync (Secondary)

Keep Spec-Kit and SpecFact synchronized automatically.

### One-Time Sync

```bash
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional
```

**What it does**:

- Syncs Spec-Kit artifacts → SpecFact project bundles
- Syncs SpecFact project bundles → Spec-Kit artifacts
- Resolves conflicts automatically (SpecFact takes priority)

**When to use**:

- After migrating from Spec-Kit
- When you want to keep both tools in sync
- Before making changes in either tool

### Watch Mode (Continuous Sync)

```bash
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch --interval 5
```

**What it does**:

- Monitors file system for changes
- Automatically syncs when files are created/modified
- Runs continuously until interrupted (Ctrl+C)

**When to use**:

- During active development
- When multiple team members use both tools
- For real-time synchronization

**Example**:

```bash
# Terminal 1: Start watch mode
specfact sync bridge --adapter speckit --bundle my-project --repo . --bidirectional --watch --interval 5

# Terminal 2: Make changes in Spec-Kit
echo "# New Feature" >> specs/002-new-feature/spec.md

# Watch mode automatically detects and syncs
# Output: "Detected 1 change(s), syncing..."
```

### What Gets Synced

- `specs/[###-feature-name]/spec.md` ↔ `.specfact/projects/<bundle-name>/features/FEATURE-*.yaml`
- `specs/[###-feature-name]/plan.md` ↔ `.specfact/projects/<bundle-name>/product.yaml`
- `specs/[###-feature-name]/tasks.md` ↔ `.specfact/projects/<bundle-name>/features/FEATURE-*.yaml`
- `.specify/memory/constitution.md` ↔ SpecFact business context (business.yaml)
- `specs/[###-feature-name]/contracts/*.yaml` ↔ `.specfact/protocols/*.yaml`

**Note**: When syncing from SpecFact to Spec-Kit, all required Spec-Kit fields (frontmatter, INVSEST criteria, Constitution Check, Phases, Technology Stack, Story mappings) are automatically generated. No manual editing required - generated artifacts are ready for `/speckit.analyze`.

---

## Repository Sync Workflow

Keep plan artifacts updated as code changes.

### One-Time Repository Sync

```bash
specfact sync repository --repo . --target .specfact
```

**What it does**:

- Analyzes code changes
- Updates plan artifacts
- Detects deviations from manual plans

**When to use**:

- After making code changes
- Before comparing plans
- To update auto-derived plans

### Repository Watch Mode (Continuous Sync)

```bash
specfact sync repository --repo . --watch --interval 5
```

**What it does**:

- Monitors code files for changes
- Automatically updates plan artifacts
- Triggers sync when files are created/modified/deleted

**When to use**:

- During active development
- For real-time plan updates
- When code changes frequently

**Example**:

```bash
# Terminal 1: Start watch mode
specfact sync repository --repo . --watch --interval 5

# Terminal 2: Make code changes
echo "class NewService:" >> src/new_service.py

# Watch mode automatically detects and syncs
# Output: "Detected 1 change(s), syncing..."
```

---

## Enforcement Workflow

Progressive enforcement from observation to blocking.

### Step 1: Shadow Mode (Observe Only)

```bash
specfact enforce stage --preset minimal
```

**What it does**:

- Sets enforcement to LOG only
- Observes violations without blocking
- Collects metrics and reports

**When to use**:

- Initial setup
- Understanding current state
- Baseline measurement

### Step 2: Balanced Mode (Warn on Issues)

```bash
specfact enforce stage --preset balanced
```

**What it does**:

- BLOCKs HIGH severity violations
- WARNs on MEDIUM severity violations
- LOGs LOW severity violations

**When to use**:

- After stabilization period
- When ready for warnings
- Before production deployment

### Step 3: Strict Mode (Block Everything)

```bash
specfact enforce stage --preset strict
```

**What it does**:

- BLOCKs all violations (HIGH, MEDIUM, LOW)
- Enforces all rules strictly
- Production-ready enforcement

**When to use**:

- Production environments
- After full validation
- When all issues are resolved

### Running Validation

```bash
# First-time setup: Configure CrossHair for contract exploration
specfact repro setup

# Quick validation
specfact repro

# Verbose validation with budget
specfact repro --verbose --budget 120

# Apply auto-fixes
specfact repro --fix --budget 120
```

**What it does**:

- `repro setup` configures CrossHair for contract exploration (one-time setup)
- `repro` validates contracts
- Checks types
- Detects async anti-patterns
- Validates state machines
- Applies auto-fixes (if available)

---

## Plan Comparison Workflow

Compare manual plans vs auto-derived plans to detect deviations.

### Quick Comparison

```bash
specfact plan compare --bundle legacy-api
```

**What it does**:

- Compares two project bundles (manual vs auto-derived)
- Finds bundles in `.specfact/projects/`
- Compares and reports deviations

**When to use**:

- After code changes
- Before merging PRs
- Regular validation

### Detailed Comparison

```bash
specfact plan compare \
  --manual .specfact/projects/manual-plan \
  --auto .specfact/projects/auto-derived \
  --out comparison-report.md
```

**Note**: Commands accept bundle directory paths, not individual files.

**What it does**:

- Compares specific plans
- Generates detailed report
- Shows all deviations with severity

**When to use**:

- Investigating specific deviations
- Generating reports for review
- Deep analysis

### Code vs Plan Comparison

```bash
specfact plan compare --bundle legacy-api --code-vs-plan
```

**What it does**:

- Compares current code state vs manual plan
- Auto-derives plan from code
- Compares in one command

**When to use**:

- Quick drift detection
- Before committing changes
- CI/CD validation

---

## Daily Development Workflow

Typical workflow for daily development.

### Morning: Check Status

```bash
# Validate everything
specfact repro --verbose

# Compare plans
specfact plan compare --bundle legacy-api
```

**What it does**:

- Validates current state
- Detects any deviations
- Reports issues

### During Development: Watch Mode

```bash
# Start watch mode for repository sync
specfact sync repository --repo . --watch --interval 5
```

**What it does**:

- Monitors code changes
- Updates plan artifacts automatically
- Keeps plans in sync

### Before Committing: Validate

```bash
# Run validation
specfact repro

# Compare plans
specfact plan compare --bundle legacy-api
```

**What it does**:

- Ensures no violations
- Detects deviations
- Validates contracts

### After Committing: CI/CD

```bash
# CI/CD pipeline runs
specfact repro --verbose --budget 120
```

**What it does**:

- Validates in CI/CD
- Blocks merges on violations
- Generates reports

---

## Migration Workflow

Complete workflow for migrating from Spec-Kit.

### Step 1: Preview

```bash
specfact import from-bridge --adapter speckit --repo . --dry-run
```

**What it does**:

- Analyzes Spec-Kit project using bridge architecture
- Shows what will be imported
- Does not modify anything

### Step 2: Execute

```bash
specfact import from-bridge --adapter speckit --repo . --write
```

**What it does**:

- Imports Spec-Kit artifacts using bridge architecture
- Creates modular project bundle structure
- Converts to SpecFact format (multiple aspect files)

### Step 3: Set Up Sync

```bash
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch --interval 5
```

**What it does**:

- Enables bidirectional sync
- Keeps both tools in sync
- Monitors for changes

### Step 4: Enable Enforcement

```bash
# Start in shadow mode
specfact enforce stage --preset minimal

# After stabilization, enable warnings
specfact enforce stage --preset balanced

# For production, enable strict mode
specfact enforce stage --preset strict
```

**What it does**:

- Progressive enforcement
- Gradual rollout
- Production-ready

---

## Related Documentation

- **[Integration Showcases](../examples/integration-showcases/)** ⭐ - Real bugs fixed via VS Code, Cursor, GitHub Actions integrations
- [Use Cases](use-cases.md) - Detailed use case scenarios
- [Command Reference](../reference/commands.md) - All commands with examples
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [IDE Integration](ide-integration.md) - Set up slash commands

---

**Happy building!** 🚀
