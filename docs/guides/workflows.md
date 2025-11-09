# Common Workflows

Daily workflows for using SpecFact CLI effectively.

## Bidirectional Sync

Keep Spec-Kit and SpecFact synchronized automatically.

### One-Time Sync

```bash
specfact sync spec-kit --repo . --bidirectional
```

**What it does**:

- Syncs Spec-Kit artifacts → SpecFact plans
- Syncs SpecFact plans → Spec-Kit artifacts
- Resolves conflicts automatically (SpecFact takes priority)

**When to use**:

- After migrating from Spec-Kit
- When you want to keep both tools in sync
- Before making changes in either tool

### Watch Mode (Continuous Sync)

```bash
specfact sync spec-kit --repo . --bidirectional --watch --interval 5
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
specfact sync spec-kit --repo . --bidirectional --watch --interval 5

# Terminal 2: Make changes in Spec-Kit
echo "# New Feature" >> specs/002-new-feature/spec.md

# Watch mode automatically detects and syncs
# Output: "Detected 1 change(s), syncing..."
```

### What Gets Synced

- `specs/[###-feature-name]/spec.md` ↔ `.specfact/plans/*.yaml`
- `specs/[###-feature-name]/plan.md` ↔ `.specfact/plans/*.yaml`
- `specs/[###-feature-name]/tasks.md` ↔ `.specfact/plans/*.yaml`
- `.specify/memory/constitution.md` ↔ SpecFact business context
- `specs/[###-feature-name]/contracts/*.yaml` ↔ `.specfact/protocols/*.yaml`

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
# Quick validation
specfact repro

# Verbose validation with budget
specfact repro --verbose --budget 120

# Apply auto-fixes
specfact repro --fix --budget 120
```

**What it does**:

- Validates contracts
- Checks types
- Detects async anti-patterns
- Validates state machines
- Applies auto-fixes (if available)

---

## Plan Comparison Workflow

Compare manual plans vs auto-derived plans to detect deviations.

### Quick Comparison

```bash
specfact plan compare --repo .
```

**What it does**:

- Finds manual plan (`.specfact/plans/main.bundle.yaml`)
- Finds latest auto-derived plan (`.specfact/reports/brownfield/auto-derived.*.yaml`)
- Compares and reports deviations

**When to use**:

- After code changes
- Before merging PRs
- Regular validation

### Detailed Comparison

```bash
specfact plan compare \
  --manual .specfact/plans/main.bundle.yaml \
  --auto .specfact/reports/brownfield/auto-derived.2025-11-09T21-00-00.bundle.yaml \
  --output comparison-report.md
```

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
specfact plan compare --code-vs-plan --repo .
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
specfact plan compare --repo .
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
specfact plan compare --repo .
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
specfact import from-spec-kit --repo . --dry-run
```

**What it does**:

- Analyzes Spec-Kit project
- Shows what will be imported
- Does not modify anything

### Step 2: Execute

```bash
specfact import from-spec-kit --repo . --write
```

**What it does**:

- Imports Spec-Kit artifacts
- Creates SpecFact structure
- Converts to SpecFact format

### Step 3: Set Up Sync

```bash
specfact sync spec-kit --repo . --bidirectional --watch --interval 5
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

- [Use Cases](use-cases.md) - Detailed use case scenarios
- [Command Reference](../reference/commands.md) - All commands with examples
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [IDE Integration](ide-integration.md) - Set up slash commands

---

**Happy building!** 🚀
